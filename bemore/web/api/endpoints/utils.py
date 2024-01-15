from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from bemore.web.api.deps import get_current_active_superuser
from bemore.models import Message
from bemore.utils import send_test_email

router = APIRouter()


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    send_test_email(email_to=email_to)
    return Message(message="Test email sent")
