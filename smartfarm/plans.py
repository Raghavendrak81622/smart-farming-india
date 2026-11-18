"""Save explicit, local snapshots with the farmer's scenario assumptions."""
from collections import OrderedDict
from contextlib import closing
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal
from uuid import UUID, uuid4
import json
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/plans")
DATABASE = Path(__file__).resolve().parents[1] / "data" / "fieldwise-plans.sqlite"
DRAFT_LIMIT = 80
drafts = OrderedDict()
lock = Lock()
Money = Annotated[float, Field(ge=0, le=1_000_000_000)]
Item = Literal["land", "seed", "fertilizer", "protection", "irrigation",
               "labour", "machinery", "harvest", "transport", "other"]


class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    price: float | None = Field(default=None, ge=0, le=1_000_000)
    total: Money | None = None
    items: dict[Item, Money] = Field(default_factory=dict)
    use_items: bool = False


class SavePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    budgets: dict[str, Budget] = Field(default_factory=dict, max_length=5)


def register_draft(snapshot):
    plan = {**snapshot, "id": str(uuid4())}
    with lock:
        if len(drafts) >= DRAFT_LIMIT:
            drafts.popitem(last=False)
        drafts[plan["id"]] = plan
    return plan


def connect():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, snapshot TEXT NOT NULL
    )""")
    return db


@router.get("")
def list_plans():
    with closing(connect()) as db:
        rows = db.execute("""SELECT id,created_at,json_extract(snapshot,'$.location.district'),
                            json_extract(snapshot,'$.location.state'),json_extract(snapshot,'$.season'),
                            json_extract(snapshot,'$.acres') FROM plans ORDER BY created_at DESC""").fetchall()
    return [dict(zip(("id", "created_at", "district", "state", "season", "acres"), row)) for row in rows]


def stored_plan(db, plan_id):
    row = db.execute("SELECT snapshot FROM plans WHERE id=?", (plan_id,)).fetchone()
    return json.loads(row[0]) if row else None


@router.get("/{plan_id}")
def read_plan(plan_id: UUID):
    with closing(connect()) as db:
        plan = stored_plan(db, str(plan_id))
    if not plan:
        raise HTTPException(404, "This plan is not saved on this device.")
    return plan


@router.post("")
def save_plan(request: SavePlan):
    plan_id = str(request.id)
    with lock:
        draft = drafts.get(plan_id)
    with closing(connect()) as db, db:
        plan = draft or stored_plan(db, plan_id)
        if not plan:
            raise HTTPException(404, "This draft expired. Generate a new plan to save it.")
        crop_ids = {crop["crop"] for crop in plan["crops"]}
        if not request.budgets.keys() <= crop_ids:
            raise HTTPException(422, "Budgets must belong to crops in this plan.")
        saved = {**plan, "budgets": {key: budget.model_dump() for key, budget in request.budgets.items()}}
        db.execute("""INSERT INTO plans VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET snapshot=excluded.snapshot""",
                   (plan_id, saved["created_at"], json.dumps(saved, ensure_ascii=False)))
    return saved
