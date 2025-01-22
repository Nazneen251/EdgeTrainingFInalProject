from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message
from django.db.models import Q
from django.utils.timezone import make_aware
from datetime import datetime

@login_required
def chat_room(request, room_name):
    search_query = request.GET.get('search', '')
    
    # Exclude the current user from the user list
    users = User.objects.exclude(id=request.user.id)

    # Fetch messages for the chat room, optionally filtered by the search query
    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver__username=room_name)) |
        (Q(receiver=request.user) & Q(sender__username=room_name))
    )
    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))

    chats = chats.order_by('timestamp')

    # Pre-fetch all messages involving the current user
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver')

    user_last_messages = []
    for user in users:
        # Filter pre-fetched messages to find the last message for each user
        last_message = next(
            (msg for msg in all_messages if (msg.sender == user or msg.receiver == user)),
            None
        )
        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })

    # Use timezone-aware datetime.min
    aware_min_datetime = make_aware(datetime.min)

    # Sort user_last_messages by the timestamp of the last_message in descending order
    user_last_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else aware_min_datetime,
        reverse=True
    )

    return render(request, 'chat.html', {
        'room_name': room_name,
        'chats': chats,
        'users': users,
        'user_last_messages': user_last_messages,
        'search_query': search_query
    })
