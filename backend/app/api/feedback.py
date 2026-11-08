from fastapi import APIRouter, Depends

from app.core.security import current_user, rate_limit
from app.db.session import get_db
from app.models.entities import Feedback
from app.schemas.beta import FeedbackInput

router = APIRouter(prefix="/feedback", tags=["Beta feedback"])


@router.post("", status_code=201)
def submit(data: FeedbackInput, user=Depends(current_user), db=Depends(get_db)):
    rate_limit("feedback:" + str(user.id), 5, 86400)
    db.add(Feedback(user_id=user.id, category=data.category, message=data.message.strip()))
    db.commit()
    return {"message": "Thank you. Your feedback has been saved for the beta team."}
