from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import (
    Analytic, Device, AnalyticDevice, SocialMediaAccount, 
    SocialMediaFollower, SocialMediaPost, SocialMediaChat, SocialMediaMessage
)
from collections import defaultdict
from typing import Optional, List
import json

router = APIRouter()

@router.get("/analytic/{analytic_id}/social-media-accounts")
def get_social_media_accounts(
    analytic_id: int,
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    query = db.query(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    )
    
    if platform:
        query = query.filter(SocialMediaAccount.platform.ilike(f"%{platform}%"))
    
    accounts = query.order_by(SocialMediaAccount.id).all()
    
    platform_data = defaultdict(list)
    for account in accounts:
        platform_data[account.platform].append({
            "account_id": account.id,
            "device_id": account.device_id,
            "username": account.username,
            "display_name": account.display_name,
            "user_id": account.user_id,
            "profile_url": account.profile_url,
            "following_count": account.following_count,
            "followers_count": account.followers_count,
            "is_verified": account.is_verified,
            "is_private": account.is_private,
            "is_active": account.is_active,
            "bio": account.bio,
            "location": account.location,
            "website": account.website,
            "last_activity": account.last_activity,
            "created_at": account.created_at
        })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Social media accounts retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "platforms": dict(platform_data),
                "summary": {
                    "total_accounts": len(accounts),
                    "platforms_count": len(platform_data),
                    "platforms": list(platform_data.keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/social-media-followers")
def get_social_media_followers(
    analytic_id: int,
    platform: Optional[str] = Query(None),
    relationship_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    query = db.query(SocialMediaFollower).join(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    )
    
    if platform:
        query = query.filter(SocialMediaAccount.platform.ilike(f"%{platform}%"))
    
    if relationship_type:
        query = query.filter(SocialMediaFollower.relationship_type == relationship_type)
    
    followers = query.order_by(SocialMediaFollower.id).all()
    
    platform_data = defaultdict(lambda: defaultdict(list))
    for follower in followers:
        platform_data[follower.account.platform][follower.relationship_type].append({
            "follower_id": follower.id,
            "account_id": follower.account_id,
            "follower_username": follower.follower_username,
            "follower_display_name": follower.follower_display_name,
            "follower_user_id": follower.follower_user_id,
            "follower_profile_url": follower.follower_profile_url,
            "relationship_type": follower.relationship_type,
            "is_verified": follower.is_verified,
            "is_private": follower.is_private,
            "follower_count": follower.follower_count,
            "following_count": follower.following_count,
            "created_at": follower.created_at
        })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Social media followers retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "platforms": dict(platform_data),
                "summary": {
                    "total_followers": len(followers),
                    "platforms_count": len(platform_data),
                    "platforms": list(platform_data.keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/social-media-chats")
def get_social_media_chats(
    analytic_id: int,
    platform: Optional[str] = Query(None),
    chat_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    query = db.query(SocialMediaChat).join(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    )
    
    if platform:
        query = query.filter(SocialMediaAccount.platform.ilike(f"%{platform}%"))
    
    if chat_type:
        query = query.filter(SocialMediaChat.chat_type == chat_type)
    
    chats = query.order_by(SocialMediaChat.id).all()
    
    platform_data = defaultdict(list)
    for chat in chats:
        platform_data[chat.account.platform].append({
            "chat_id": chat.id,
            "account_id": chat.account_id,
            "chat_id_string": chat.chat_id,
            "chat_type": chat.chat_type,
            "chat_name": chat.chat_name,
            "participants": chat.participants,
            "total_messages": chat.total_messages,
            "sent_messages": chat.sent_messages,
            "received_messages": chat.received_messages,
            "first_message_at": chat.first_message_at,
            "last_message_at": chat.last_message_at,
            "created_at": chat.created_at
        })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Social media chats retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "platforms": dict(platform_data),
                "summary": {
                    "total_chats": len(chats),
                    "platforms_count": len(platform_data),
                    "platforms": list(platform_data.keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/social-media-posts")
def get_social_media_posts(
    analytic_id: int,
    platform: Optional[str] = Query(None),
    post_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    query = db.query(SocialMediaPost).join(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    )
    
    if platform:
        query = query.filter(SocialMediaAccount.platform.ilike(f"%{platform}%"))
    
    if post_type:
        query = query.filter(SocialMediaPost.post_type == post_type)
    
    posts = query.order_by(SocialMediaPost.id).limit(limit).all()
    
    platform_data = defaultdict(list)
    for post in posts:
        platform_data[post.account.platform].append({
            "post_id": post.id,
            "account_id": post.account_id,
            "post_id_string": post.post_id,
            "post_type": post.post_type,
            "content": post.content,
            "media_urls": post.media_urls,
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "shares_count": post.shares_count,
            "views_count": post.views_count,
            "posted_at": post.posted_at,
            "location": post.location,
            "hashtags": post.hashtags,
            "mentions": post.mentions,
            "created_at": post.created_at
        })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Social media posts retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "platforms": dict(platform_data),
                "summary": {
                    "total_posts": len(posts),
                    "platforms_count": len(platform_data),
                    "platforms": list(platform_data.keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/social-media-correlation")
def get_social_media_correlation(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_id": d.id,
            "device_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_type": d.device_type,
            "device_model": d.device_model
        }
        for d in devices
    }

    accounts = db.query(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    ).order_by(SocialMediaAccount.id).all()

    followers = db.query(SocialMediaFollower).join(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    ).order_by(SocialMediaFollower.id).all()

    chats = db.query(SocialMediaChat).join(SocialMediaAccount).filter(
        SocialMediaAccount.device_id.in_(device_ids)
    ).order_by(SocialMediaChat.id).all()

    correlations = []
    
    follower_devices = defaultdict(list)
    for follower in followers:
        follower_devices[follower.follower_username].append({
            "device_id": follower.account.device_id,
            "device_name": device_info.get(follower.account.device_id, {}).get("device_name", f"Device {follower.account.device_id}"),
            "platform": follower.account.platform,
            "relationship_type": follower.relationship_type
        })
    
    for username, devices in follower_devices.items():
        if len(devices) >= 2:
            correlations.append({
                "type": "follower_correlation",
                "username": username,
                "platforms": list(set(d["platform"] for d in devices)),
                "devices": devices,
                "correlation_strength": len(devices)
            })
    
    chat_correlations = defaultdict(list)
    for chat in chats:
        if chat.participants:
            try:
                participants = json.loads(chat.participants) if isinstance(chat.participants, str) else chat.participants
                for participant in participants:
                    chat_correlations[participant].append({
                        "device_id": chat.account.device_id,
                        "device_name": device_info.get(chat.account.device_id, {}).get("device_name", f"Device {chat.account.device_id}"),
                        "platform": chat.account.platform,
                        "chat_type": chat.chat_type,
                        "message_count": chat.total_messages
                    })
            except:
                pass
    
    for participant, devices in chat_correlations.items():
        if len(devices) >= 2:
            correlations.append({
                "type": "chat_correlation",
                "participant": participant,
                "platforms": list(set(d["platform"] for d in devices)),
                "devices": devices,
                "correlation_strength": len(devices)
            })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Social media correlation analysis completed",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "devices": list(device_info.values()),
                "correlations": correlations,
                "summary": {
                    "total_accounts": len(accounts),
                    "total_followers": len(followers),
                    "total_chats": len(chats),
                    "correlations_found": len(correlations),
                    "follower_correlations": len([c for c in correlations if c["type"] == "follower_correlation"]),
                    "chat_correlations": len([c for c in correlations if c["type"] == "chat_correlation"])
                }
            }
        },
        status_code=200
    )
