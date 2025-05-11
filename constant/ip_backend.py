
ip_backend = '37fe-2a09-bac5-d46a-16d2-00-246-fa.ngrok-free.app/gym-pose/ws'

def uri_backend(userId, exerciseId, workoutSummaryId):
    
    if workoutSummaryId == None:
        ws_uri = f"wss://{ip_backend}?userId={userId}&exerciseId={exerciseId}&workoutSummaryId=unknown"
    else:
        ws_uri = f"wss://{ip_backend}?userId={userId}&exerciseId={exerciseId}&workoutSummaryId={workoutSummaryId}"
        
    return ws_uri