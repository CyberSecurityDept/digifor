from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/landing")
async def get_landing_page():
    return {
        "status": 200,
        "message": "Landing page data retrieved successfully",
        "data": {
            "user_type": "default",
            "available_modules": [
                {
                    "id": "analytics",
                    "name": "Analytics",
                    "description": "Digital forensics analytics and reporting",
                    "endpoint": "/api/v1/analytics",
                    "icon": "analytics",
                    "enabled": True
                },
                {
                    "id": "case_management",
                    "name": "Case Management",
                    "description": "Case management and investigation tracking",
                    "endpoint": "/api/v1/cases",
                    "icon": "case",
                    "enabled": True
                }
            ],
            "navigation": {
                "analytics": {
                    "title": "Analytics",
                    "description": "Access digital forensics analytics",
                    "url": "/analytics"
                },
                "case_management": {
                    "title": "Case Management",
                    "description": "Manage cases and investigations",
                    "url": "/cases"
                }
            }
        }
    }


