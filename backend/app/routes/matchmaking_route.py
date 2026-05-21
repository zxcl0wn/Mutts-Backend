from fastapi import APIRouter, Depends, HTTPException, status
from ..auth.utils.auth_utils import verify_token
from ..core.dependencies import get_matchmaking_service
from ..services.matchmaking_service import MatchmakingService


router = APIRouter(
    prefix="/matchmaking"
)


@router.post("/join")
async def join_queue(
    access_token: str,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service)
):
    """Встать в очередь поиска игры"""
    try:
        username = await verify_token(access_token)
        result = await matchmaking_service.join_queue(username)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/leave")
async def leave_queue(
    access_token: str,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service)
):
    """Выйти из очереди поиска"""
    try:
        username = await verify_token(access_token)
        result = await matchmaking_service.leave_queue(username)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status")
async def get_status(
    access_token: str,
    matchmaking_service: MatchmakingService = Depends(get_matchmaking_service)
):
    """Проверить статус поиска игры"""
    try:
        username = await verify_token(access_token)
        result = await matchmaking_service.get_queue_status(username)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
