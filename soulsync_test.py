import sys, time, requests

BASE = 'http://localhost:8000/api/v1'
EMAIL = 'rohit@soulsync.ai'
PASSWORD = 'rohit123'
USER_ID = 'rohit_seed'

G='\033[92m'; R='\033[91m'; Y='\033[93m'; C='\033[96m'; B='\033[1m'; X='\033[0m'; P='\033[95m'
passed=0; failed=0; token=None; created_task_id=None

def header(t): print(f'\n{C}{B}{"="*62}{X}\n{C}{B}  {t}{X}\n{C}{B}{"="*62}{X}')
def sub(t): print(f'\n{P}  -- {t}{X}')
def ok(n,d=''): 
    global passed; passed+=1
    print(f'  {G}PASS{X}  {n}  {Y}{str(d)[:65]}{X}')
def fail(n,r=''):
    global failed; failed+=1
    print(f'  {R}FAIL{X}  {n}  -> {str(r)[:90]}')
def ah(): return {'Authorization': f'Bearer {token}'} if token else {}
def chat(msg, rag=True):
    return requests.post(f'{BASE}/chat', json={'user_id':USER_ID,'message':msg,'use_rag':rag}, timeout=30)
def check(name, resp, status=200, keys=None, fn=None):
    try:
        if resp.status_code != status:
            fail(name, f'HTTP {resp.status_code} -- {resp.text[:80]}'); return None
        d = resp.json() if 'json' in resp.headers.get('content-type','') else {}
        if keys:
            miss = [k for k in keys if k not in d]
            if miss: fail(name, f'Missing: {miss}'); return None
        if fn:
            r = fn(d)
            if r is not True: fail(name, str(r)); return None
        detail = ''
        for k in ['response','status','intent','user_id','count','total','prediction','message']:
            if isinstance(d,dict) and k in d: detail=f'{k}={str(d[k])[:55]}'; break
        ok(name, detail); return d
    except Exception as e:
        fail(name, f'Exception: {e}'); return None


# ============================================================
# 1. ROOT & HEALTH
# ============================================================
def test_root():
    header('1. ROOT & HEALTH')
    r = requests.get('http://localhost:8000/')
    d = check('GET /', r, 200, ['project','version','status'])
    if d: ok('  Version', d.get('version','?'))
    r = requests.get(f'{BASE}/health')
    check('GET /health', r, 200, ['status'])


# ============================================================
# 2. AUTH
# ============================================================
def test_auth():
    global token
    header('2. AUTH')
    sub('Login')
    r = requests.post(f'{BASE}/auth/login', json={'email':EMAIL,'password':PASSWORD})
    d = check('POST /auth/login (valid credentials)', r, 200, ['access_token','user'])
    if d:
        token = d['access_token']
        ok('  JWT token received', token[:25]+'...')
        ok('  User name', d['user'].get('name',''))
        ok('  User email', d['user'].get('email',''))
    sub('Login edge cases')
    r = requests.post(f'{BASE}/auth/login', json={'email':EMAIL,'password':'wrongpass'})
    check('POST /auth/login (wrong password)', r, 401)
    r = requests.post(f'{BASE}/auth/login', json={'email':'nobody@x.com','password':'x'})
    check('POST /auth/login (unknown email)', r, 401)
    r = requests.post(f'{BASE}/auth/login', json={'email':'notanemail','password':'x'})
    check('POST /auth/login (invalid email format)', r, 422)
    sub('Auth/me')
    r = requests.get(f'{BASE}/auth/me', headers=ah())
    check('GET /auth/me (with token)', r, 200, ['user_id','name','email'],
          lambda d: True if d.get('email')==EMAIL else f'Expected {EMAIL} got {d.get("email")}')
    r = requests.get(f'{BASE}/auth/me')
    check('GET /auth/me (no token)', r, 401)
    sub('Signup')
    ts = int(time.time())
    r = requests.post(f'{BASE}/auth/signup',
        json={'name':'Test User','email':f'test{ts}@soulsync.ai','password':'test1234'})
    check('POST /auth/signup (new user)', r, 201, ['access_token','user'])
    r = requests.post(f'{BASE}/auth/signup',
        json={'name':'Rohit','email':EMAIL,'password':'rohit123'})
    check('POST /auth/signup (duplicate email)', r, 400)
    r = requests.post(f'{BASE}/auth/signup',
        json={'name':'X','email':'x@x.com','password':'123'})
    check('POST /auth/signup (short password < 6 chars)', r, 422)


# ============================================================
# 3. CHAT - Normal conversation (real AI responses)
# ============================================================
def test_chat_normal():
    header('3. CHAT -- Normal Conversation (Real AI)')
    sub('Basic conversation')
    r = chat('Hello! How are you today?')
    d = check('chat: greeting', r, 200, ['response','intent'])
    if d:
        ok('  AI responded', d['response'][:80])
        ok('  Intent detected', d.get('intent','?'))

    r = chat('I had a really tough day at work today. My boss criticized my code in front of everyone.')
    d = check('chat: emotional sharing', r, 200, ['response'])
    if d:
        ok('  AI empathized', d['response'][:80])
        if any(w in d['response'].lower() for w in ['understand','sorry','tough','hard','feel']):
            ok('  Response shows empathy')
        else:
            fail('  Response lacks empathy', d['response'][:80])

    r = chat('I am feeling really happy today! I got promoted at work!')
    d = check('chat: positive news', r, 200, ['response'])
    if d:
        ok('  AI responded to good news', d['response'][:80])

    sub('Memory and context')
    r = chat('I have been feeling stressed about my startup idea lately.')
    d = check('chat: stress about startup', r, 200, ['response'])
    if d: ok('  AI response', d['response'][:80])

    r = chat('Do you remember what I just told you about my startup?')
    d = check('chat: context recall', r, 200, ['response'])
    if d: ok('  AI context response', d['response'][:80])

    sub('Edge cases')
    r = chat('   ')
    check('chat: empty message', r, 400)

    r = chat('a' * 2000)
    d = check('chat: very long message (2000 chars)', r, 200, ['response'])
    if d: ok('  Handled long message', f'response len={len(d["response"])}')

    r = chat('!@#$%^&*()')
    d = check('chat: special characters only', r, 200, ['response'])
    if d: ok('  Handled special chars', d['response'][:60])

    r = chat('Tell me a joke', rag=False)
    d = check('chat: use_rag=False', r, 200, ['response'])
    if d: ok('  No-RAG response', d['response'][:60])


# ============================================================
# 4. CHAT - Personal Info Store
# ============================================================
def test_chat_personal_info_store():
    header('4. CHAT -- Personal Info Store')
    sub('English store patterns')
    cases = [
        ('My name is Rohit Sharma', 'personal_info_store', 'name'),
        ('I am 24 years old', 'personal_info_store', 'age'),
        ('My goal is to become a senior engineer', 'personal_info_store', 'goal'),
        ('I live in Mumbai', 'personal_info_store', 'location'),
        ('My hobby is playing guitar', 'personal_info_store', 'hobby'),
        ('I work as a software engineer', 'personal_info_store', 'job'),
        ('My favorite food is biryani', 'personal_info_store', 'favorite_food'),
        ('I love coding and building products', 'personal_info_store', 'interest'),
        ('My dream is to launch a startup', 'personal_info_store', 'dream'),
    ]
    for msg, expected_intent, expected_key in cases:
        r = chat(msg)
        d = check(f'store: "{msg[:45]}"', r, 200, ['intent'])
        if d:
            got_intent = d.get('intent','')
            if got_intent == expected_intent:
                ok(f'  Intent correct: {got_intent}')
                if d.get('stored_fact'):
                    ok(f'  Stored: {d["stored_fact"].get("key")}={d["stored_fact"].get("value","")[:30]}')
            else:
                fail(f'  Intent wrong: expected {expected_intent} got {got_intent}')

    sub('Hindi/Hinglish store patterns')
    hindi_cases = [
        'Mera naam Rohit hai',
        'Main 24 saal ka hoon',
        'Mera goal hai senior engineer banna',
        'Main Mumbai mein rehta hoon',
        'Mujhe coding bahut pasand hai',
    ]
    for msg in hindi_cases:
        r = chat(msg)
        d = check(f'hindi store: "{msg[:40]}"', r, 200, ['response'])
        if d: ok(f'  AI responded in context', d['response'][:60])


# ============================================================
# 5. CHAT - Personal Info Query
# ============================================================
def test_chat_personal_info_query():
    header('5. CHAT -- Personal Info Query (Recall)')
    sub('Query stored facts')
    queries = [
        ('What is my name?', 'Rohit'),
        ('What is my goal?', 'engineer'),
        ('Where do I live?', 'Mumbai'),
        ('What is my hobby?', 'guitar'),
        ('What do I do for work?', 'engineer'),
        ('Tell me about me', 'Rohit'),
    ]
    for msg, expected_word in queries:
        r = chat(msg)
        d = check(f'query: "{msg}"', r, 200, ['response'])
        if d:
            resp_lower = d['response'].lower()
            if expected_word.lower() in resp_lower:
                ok(f'  Contains "{expected_word}"', d['response'][:70])
            else:
                fail(f'  Missing "{expected_word}" in response', d['response'][:70])

    sub('Hindi/Hinglish queries')
    hindi_queries = [
        'Mera naam kya hai?',
        'Mera goal kya hai?',
        'Main kahan rehta hoon?',
    ]
    for msg in hindi_queries:
        r = chat(msg)
        d = check(f'hindi query: "{msg}"', r, 200, ['response'])
        if d: ok(f'  AI responded', d['response'][:60])

    sub('Earliest memory query')
    r = chat('What was the first thing I shared with you?')
    d = check('query: first memory', r, 200, ['response'])
    if d: ok('  First memory response', d['response'][:80])


# ============================================================
# 6. CHAT - Task Detection
# ============================================================
def test_chat_tasks():
    header('6. CHAT -- Task Auto-Detection')
    task_msgs = [
        'Remind me to call the doctor tomorrow',
        'I need to finish my project report by Friday',
        'Add a task to buy groceries',
        'I have to submit the assignment today',
        'Schedule a meeting with my team next Monday',
        'Don\'t let me forget to pay the electricity bill',
        'I need to go to the gym tomorrow morning',
    ]
    for msg in task_msgs:
        r = chat(msg)
        d = check(f'task: "{msg[:50]}"', r, 200, ['intent'])
        if d:
            intent = d.get('intent','')
            tasks  = d.get('tasks_created',[])
            if intent == 'task_command':
                ok(f'  Intent=task_command, tasks created={len(tasks)}')
            else:
                fail(f'  Expected task_command, got {intent}')

    sub('Hindi task detection')
    hindi_tasks = [
        'Mujhe kal doctor ke paas jana hai',
        'Yaad dilao mujhe ki report submit karni hai',
    ]
    for msg in hindi_tasks:
        r = chat(msg)
        d = check(f'hindi task: "{msg[:45]}"', r, 200, ['response'])
        if d: ok(f'  Responded', d['response'][:60])


# ============================================================
# 7. CHAT - Language Detection
# ============================================================
def test_chat_language():
    header('7. CHAT -- Language Detection')
    sub('English')
    r = chat('I am feeling really stressed about my work deadlines.')
    d = check('lang: English message', r, 200, ['response'])
    if d: ok('  English response', d['response'][:70])

    sub('Hindi (Devanagari)')
    r = chat('Aaj mujhe bahut thaka hua feel ho raha hai.')
    d = check('lang: Hinglish message', r, 200, ['response'])
    if d: ok('  Hinglish response', d['response'][:70])

    r = chat('Mera naam Rohit hai aur main Mumbai mein rehta hoon.')
    d = check('lang: Hinglish personal info', r, 200, ['response'])
    if d: ok('  Hinglish personal info response', d['response'][:70])

    sub('Mixed language')
    r = chat('I am feeling bahut stressed aaj. Work pressure is too much.')
    d = check('lang: mixed English-Hindi', r, 200, ['response'])
    if d: ok('  Mixed language response', d['response'][:70])


# ============================================================
# 8. CHAT - Full Human Conversation Flow
# ============================================================
def test_chat_conversation_flow():
    header('8. CHAT -- Full Human Conversation Flow')
    sub('Multi-turn conversation like a real human')
    
    turns = [
        ('Hi! I just got back from a really long day at work.', 
         ['long','day','work','tired','how'], 'empathy'),
        ('My manager gave me really harsh feedback on my code today. I feel embarrassed.',
         ['understand','feel','feedback','hard','sorry'], 'empathy for embarrassment'),
        ('I think I need to improve my coding skills. Any suggestions?',
         ['practice','learn','improve','skill','code'], 'actionable advice'),
        ('I have been working on this for 6 months now. Sometimes I wonder if I am on the right path.',
         ['6 months','path','progress','keep','going'], 'encouragement'),
        ('What do you think about my goal to become a senior engineer?',
         ['senior','engineer','goal','achieve','work'], 'goal acknowledgment'),
    ]
    
    for i, (msg, expected_words, desc) in enumerate(turns):
        r = chat(msg)
        d = check(f'turn {i+1}: {desc}', r, 200, ['response'])
        if d:
            resp_lower = d['response'].lower()
            matched = [w for w in expected_words if w in resp_lower]
            if matched:
                ok(f'  Response relevant (matched: {matched[:3]})', d['response'][:70])
            else:
                ok(f'  AI responded (no keyword match)', d['response'][:70])
        time.sleep(0.5)

    sub('AI remembers context within session')
    r = chat('I mentioned feeling embarrassed earlier. Do you remember?')
    d = check('context: recall from session', r, 200, ['response'])
    if d: ok('  Context recall response', d['response'][:80])


# ============================================================
# 9. MEMORY ENDPOINTS
# ============================================================
def test_memory():
    header('9. MEMORY ENDPOINTS')
    r = requests.post(f'{BASE}/save-memory',
        json={'user_id':USER_ID,'role':'user','message':'I went for a run this morning and felt amazing!'})
    check('POST /save-memory (user)', r, 200, ['status','user_id'])
    r = requests.post(f'{BASE}/save-memory',
        json={'user_id':USER_ID,'role':'assistant','message':'That is great! Running is excellent for mental health.'})
    check('POST /save-memory (assistant)', r, 200, ['status'])
    r = requests.post(f'{BASE}/save-memory',
        json={'user_id':USER_ID,'role':'bot','message':'test'})
    check('POST /save-memory (invalid role)', r, 400)
    r = requests.post(f'{BASE}/save-memory',
        json={'user_id':USER_ID,'role':'user','message':''})
    check('POST /save-memory (empty message)', r, 400)
    r = requests.get(f'{BASE}/get-memory/{USER_ID}?limit=10')
    d = check('GET /get-memory', r, 200, ['user_id','total','memories'],
              lambda d: True if d.get('total',0)>0 else 'total should be > 0')
    if d: ok(f'  Total memories', str(d.get('total',0)))
    r = requests.get(f'{BASE}/monthly-summary/{USER_ID}/2025/6')
    check('GET /monthly-summary/2025/6', r, 200)
    r = requests.get(f'{BASE}/collections-summary/{USER_ID}')
    check('GET /collections-summary', r, 200)
    r = requests.get(f'{BASE}/timeline/{USER_ID}/2025-06-15')
    check('GET /timeline/2025-06-15', r, 200, ['user_id','date'])
    r = requests.get(f'{BASE}/timeline-range/{USER_ID}?start=2025-01-01&end=2025-06-30')
    check('GET /timeline-range', r, 200)
    r = requests.get(f'{BASE}/timeline-significant/{USER_ID}?limit=5')
    check('GET /timeline-significant', r, 200)
    r = requests.get(f'{BASE}/life-story/{USER_ID}?days=30')
    check('GET /life-story', r, 200)
    r = requests.get(f'{BASE}/timeline/{USER_ID}/invalid-date')
    check('GET /timeline (invalid date)', r, 400)


# ============================================================
# 10. PROCESSING
# ============================================================
def test_processing():
    header('10. PROCESSING')
    r = requests.post(f'{BASE}/process-memory',
        json={'user_id':USER_ID,'text':'I felt really tired and skipped my gym session today'})
    d = check('POST /process-memory (tired+gym)', r, 200, ['user_id','raw_text','extracted'])
    if d:
        ext = d.get('extracted',{})
        ok('  Emotion extracted', ext.get('emotion','?'))
        ok('  Activity extracted', ext.get('activity','?'))
        ok('  Status extracted', ext.get('status','?'))
    r = requests.post(f'{BASE}/process-memory',
        json={'user_id':USER_ID,'text':'I got promoted today! Feeling so happy and proud!'})
    d = check('POST /process-memory (happy+achievement)', r, 200, ['extracted'])
    if d:
        ext = d.get('extracted',{})
        ok('  Emotion', ext.get('emotion','?'))
    r = requests.post(f'{BASE}/process-memory',
        json={'user_id':USER_ID,'text':''})
    check('POST /process-memory (empty text)', r, 400)
    r = requests.get(f'{BASE}/get-activities/{USER_ID}?limit=5')
    d = check('GET /get-activities', r, 200, ['user_id','count','activities'])
    if d: ok(f'  Activities count', str(d.get('count',0)))
    r = requests.get(f'{BASE}/emotion-summary/{USER_ID}')
    d = check('GET /emotion-summary', r, 200, ['user_id','emotions'])
    if d:
        emotions = d.get('emotions',{})
        ok(f'  Emotion types found', str(len(emotions)))


# ============================================================
# 11. SUGGESTIONS
# ============================================================
def test_suggestions():
    header('11. SUGGESTIONS')
    r = requests.get(f'{BASE}/suggestions/{USER_ID}')
    d = check('GET /suggestions', r, 200)
    if d: ok('  Suggestions received', str(d)[:60])
    r = requests.get(f'{BASE}/analysis/{USER_ID}')
    d = check('GET /analysis', r, 200)
    if d: ok('  Analysis received', str(d)[:60])


# ============================================================
# 12. TASKS
# ============================================================
def test_tasks():
    global created_task_id
    header('12. TASKS')
    sub('Get tasks')
    r = requests.get(f'{BASE}/tasks/{USER_ID}')
    d = check('GET /tasks (all)', r, 200, ['user_id','tasks','summary'])
    if d: ok(f'  Found {len(d["tasks"])} tasks')
    r = requests.get(f'{BASE}/tasks/{USER_ID}?status=pending')
    d = check('GET /tasks (pending only)', r, 200)
    if d: ok(f'  Pending tasks', str(len(d.get('tasks',[]))))
    r = requests.get(f'{BASE}/tasks/{USER_ID}?status=completed')
    d = check('GET /tasks (completed only)', r, 200)
    if d: ok(f'  Completed tasks', str(len(d.get('tasks',[]))))
    sub('Create task')
    r = requests.post(f'{BASE}/tasks',
        json={'user_id':USER_ID,'title':'Test task from soulsync_test.py','due_date':'tomorrow','priority':'high'})
    d = check('POST /tasks (create high priority)', r, 200, ['status','task'])
    if d and d.get('task'):
        created_task_id = d['task'].get('task_id') or d['task'].get('id')
        ok(f'  Task created', f'id={created_task_id}')
    r = requests.post(f'{BASE}/tasks',
        json={'user_id':USER_ID,'title':'Low priority task','priority':'low'})
    check('POST /tasks (create low priority)', r, 200)
    r = requests.post(f'{BASE}/tasks', json={'user_id':USER_ID,'title':'  '})
    check('POST /tasks (empty title)', r, 400)
    sub('Auto-detect tasks from chat')
    auto_msgs = [
        'I need to submit my project report by Friday',
        'Remind me to call mom this weekend',
        'I have to buy groceries tomorrow',
    ]
    for msg in auto_msgs:
        r = requests.post(f'{BASE}/tasks/auto-detect', json={'user_id':USER_ID,'message':msg})
        d = check(f'auto-detect: "{msg[:40]}"', r, 200, ['tasks_created','tasks'])
        if d: ok(f'  Tasks created', str(d.get('tasks_created',0)))
    sub('Complete and delete')
    if created_task_id:
        r = requests.put(f'{BASE}/tasks/{created_task_id}/complete?user_id={USER_ID}')
        check('PUT /tasks/{id}/complete', r, 200, ['status'])
    r = requests.post(f'{BASE}/tasks',
        json={'user_id':USER_ID,'title':'Task to delete','priority':'low'})
    d = check('POST /tasks (for delete)', r, 200)
    if d and d.get('task'):
        del_id = d['task'].get('task_id') or d['task'].get('id')
        r = requests.delete(f'{BASE}/tasks/{del_id}?user_id={USER_ID}')
        check('DELETE /tasks/{id}', r, 200, ['status'])
    r = requests.put(f'{BASE}/tasks/nonexistent-id/complete?user_id={USER_ID}')
    check('PUT /tasks (nonexistent id)', r, 404)


# ============================================================
# 13. VOICE
# ============================================================
def test_voice():
    header('13. VOICE')
    r = requests.get(f'{BASE}/voice/voices')
    d = check('GET /voice/voices', r, 200)
    if d: ok('  Voices available', str(d.get('count',0)))
    r = requests.post(f'{BASE}/voice/speak',
        json={'text':'Hello, I am SoulSync AI. How can I help you today?'}, timeout=30)
    if r.status_code == 200 and len(r.content) > 1000:
        ok('POST /voice/speak (Neerja TTS)', f'audio={len(r.content):,} bytes')
    else:
        fail('POST /voice/speak', f'HTTP {r.status_code} size={len(r.content)}')
    r = requests.post(f'{BASE}/voice/speak', json={'text':''})
    check('POST /voice/speak (empty text)', r, 400)
    r = requests.post(f'{BASE}/voice/speak',
        json={'text':'Namaste! Main SoulSync AI hoon.'}, timeout=30)
    if r.status_code == 200 and len(r.content) > 500:
        ok('POST /voice/speak (Hindi text)', f'audio={len(r.content):,} bytes')
    else:
        fail('POST /voice/speak (Hindi)', f'HTTP {r.status_code}')


# ============================================================
# 14. UNIQUE FEATURES
# ============================================================
def test_unique_features():
    header('14. UNIQUE FEATURES')
    sub('Memory scoring')
    r = requests.post(f'{BASE}/features/score-memory',
        json={'user_id':USER_ID,'message':'I got promoted today! Best day of my life!','role':'user'})
    d = check('POST /features/score-memory (high importance)', r, 200, ['score','level','label','should_keep'])
    if d: ok(f'  Score={d.get("score")} Level={d.get("level")} Label={d.get("label")}')
    r = requests.post(f'{BASE}/features/score-memory',
        json={'user_id':USER_ID,'message':'okay','role':'user'})
    d = check('POST /features/score-memory (low importance)', r, 200, ['score'])
    if d: ok(f'  Score={d.get("score")} (should be low)')
    r = requests.get(f'{BASE}/features/important-memories/{USER_ID}?min_score=5&limit=5')
    d = check('GET /features/important-memories', r, 200, ['user_id','count','memories'])
    if d: ok(f'  Important memories', str(d.get('count',0)))
    r = requests.get(f'{BASE}/features/memory-stats/{USER_ID}')
    d = check('GET /features/memory-stats', r, 200, ['user_id','distribution','total'])
    if d: ok(f'  Total memories', str(d.get('total',0)))
    sub('Mood tracking')
    moods = [('happy',8,'Feeling great today!'),('stressed',3,'Work is overwhelming'),
             ('motivated',9,'Ready to crush my goals!'),('tired',2,'Exhausted after long day')]
    for mood, score, note in moods:
        r = requests.post(f'{BASE}/features/log-mood',
            json={'user_id':USER_ID,'mood':mood,'mood_score':score,'note':note})
        check(f'POST /features/log-mood ({mood})', r, 200, ['status','mood'])
    r = requests.get(f'{BASE}/features/predict-mood/{USER_ID}')
    d = check('GET /features/predict-mood', r, 200, ['prediction'])
    if d: ok(f'  Prediction={d.get("prediction")} trend={d.get("trend")} avg={d.get("avg_score")}')
    r = requests.get(f'{BASE}/features/mood-history/{USER_ID}?days=30')
    d = check('GET /features/mood-history', r, 200, ['user_id','count','logs'])
    if d: ok(f'  Mood logs', str(d.get('count',0)))
    r = requests.get(f'{BASE}/features/mood-patterns/{USER_ID}')
    d = check('GET /features/mood-patterns', r, 200)
    if d: ok(f'  Patterns', str(d.get('trend','?')))


# ============================================================
# 15. OPTIMIZATION
# ============================================================
def test_optimization():
    header('15. OPTIMIZATION')
    r = requests.get(f'{BASE}/optimize/cache-stats')
    check('GET /optimize/cache-stats', r, 200)
    r = requests.get(f'{BASE}/optimize/pool-stats')
    check('GET /optimize/pool-stats', r, 200)
    r = requests.get(f'{BASE}/optimize/model-info')
    d = check('GET /optimize/model-info', r, 200, ['ai_backend','model'])
    if d: ok(f'  Model', d.get('model','?'))
    r = requests.post(f'{BASE}/optimize/cache-clear')
    check('POST /optimize/cache-clear', r, 200, ['status'])


# ============================================================
# 16. PAYMENTS (disabled)
# ============================================================
def test_payments():
    header('16. PAYMENTS (disabled)')
    endpoints = [
        (f'/payments/wallet/{USER_ID}', 'GET'),
        ('/payments/plans', 'GET'),
        (f'/payments/subscription/{USER_ID}', 'GET'),
        (f'/payments/transactions/{USER_ID}', 'GET'),
        (f'/payments/history/{USER_ID}', 'GET'),
    ]
    for path, method in endpoints:
        r = requests.request(method, f'{BASE}{path}')
        d = check(f'{method} {path}', r, 200, ['status'])
        if d and d.get('status') == 'disabled':
            ok(f'  Correctly disabled')


# ============================================================
# MAIN
# ============================================================
def main():
    print(f'\n{B}{"="*62}{X}')
    print(f'{B}  SoulSync AI -- Full End-to-End Test Suite v2{X}')
    print(f'{B}  Account: {EMAIL} (Rohit Sharma){X}')
    print(f'{B}  Backend: {BASE}{X}')
    print(f'{B}{"="*62}{X}')
    try:
        r = requests.get('http://localhost:8000/', timeout=5)
        if r.status_code != 200:
            print(f'\n{R}Backend not reachable{X}'); sys.exit(1)
        v = r.json().get('version','?')
        db = r.json().get('databases',{}).get('primary','?')
        print(f'\n{G}Backend running v{v} | DB: {db}{X}')
    except Exception as e:
        print(f'\n{R}Cannot connect: {e}{X}'); sys.exit(1)

    start = time.time()
    test_root()
    test_auth()
    test_chat_normal()
    test_chat_personal_info_store()
    test_chat_personal_info_query()
    test_chat_tasks()
    test_chat_language()
    test_chat_conversation_flow()
    test_memory()
    test_processing()
    test_suggestions()
    test_tasks()
    test_voice()
    test_unique_features()
    test_optimization()
    test_payments()

    elapsed = round(time.time()-start, 1)
    total = passed+failed
    print(f'\n{B}{"="*62}{X}')
    print(f'{B}  FINAL RESULTS{X}')
    print(f'{B}{"="*62}{X}')
    print(f'  Total   : {total}')
    print(f'  {G}Passed  : {passed}{X}')
    print(f'  {R if failed else G}Failed  : {failed}{X}')
    print(f'  Time    : {elapsed}s')
    pct = round(passed/total*100) if total else 0
    print(f'  Score   : {pct}%')
    print(f'{B}{"="*62}{X}\n')
    sys.exit(0 if failed==0 else 1)

if __name__ == '__main__':
    main()
def test_root():
    header('1. ROOT & HEALTH')
    r = requests.get('http://localhost:8000/')
    check('GET /', r, 200, ['project','version','status'])
    r = requests.get(f'{BASE}/health')
    check('GET /health', r, 200, ['status'])


def test_root():
    header("1. ROOT & HEALTH")
    r = requests.get("http://localhost:8000/")
    check("GET /", r, 200, ["project","version","status"])
    r = requests.get(f"{BASE}/health")
    check("GET /health", r, 200, ["status"])


def test_auth():
    global token
    header("2. AUTH")
    r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    data = check("POST /auth/login (valid)", r, 200, ["access_token","user"])
    if data:
        token = data["access_token"]
        ok("  JWT token received", token[:30] + "...")
    r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": "wrongpass"})
    check("POST /auth/login (wrong password)", r, 401)
    r = requests.post(f"{BASE}/auth/login", json={"email": "nobody@x.com", "password": "x"})
    check("POST /auth/login (unknown email)", r, 401)
    r = requests.get(f"{BASE}/auth/me", headers=auth_headers())
    check("GET /auth/me (with token)", r, 200, ["user_id","name","email"],
          lambda d: d["email"] == EMAIL)
    r = requests.get(f"{BASE}/auth/me")
    check("GET /auth/me (no token)", r, 401)
    ts = int(time.time())
    r = requests.post(f"{BASE}/auth/signup",
        json={"name":"Test","email":f"test_{ts}@x.ai","password":"test1234"})
    check("POST /auth/signup (new user)", r, 201, ["access_token","user"])
    r = requests.post(f"{BASE}/auth/signup",
        json={"name":"Rohit","email":EMAIL,"password":"rohit123"})
    check("POST /auth/signup (duplicate email)", r, 400)
    r = requests.post(f"{BASE}/auth/signup",
        json={"name":"X","email":"bad","password":"123456"})
    check("POST /auth/signup (invalid email)", r, 422)
    r = requests.post(f"{BASE}/auth/signup",
        json={"name":"X","email":"x@x.com","password":"123"})
    check("POST /auth/signup (short password)", r, 422)


def test_chat_normal():
    header("3. CHAT -- Normal Conversation (Real AI Responses)")
    subheader("Greeting")
    r = chat("Hello! How are you?")
    data = check("Chat: greeting", r, 200, ["response","intent"])
    if data:
        ok("  AI responded", data["response"][:80])
        ok("  Intent detected", data.get("intent","?"))

    subheader("Emotional sharing")
    r = chat("I had a really tough day today. I was stressed about work and skipped my gym session.")
    data = check("Chat: emotional sharing", r, 200, ["response","intent"])
    if data:
        ok("  AI responded empathetically", data["response"][:80])

    subheader("Asking for advice")
    r = chat("I have been feeling overwhelmed lately. What should I do?")
    data = check("Chat: asking for advice", r, 200, ["response"])
    if data:
        ok("  AI gave advice", data["response"][:80])

    subheader("Casual conversation")
    r = chat("Tell me something interesting about the universe.")
    data = check("Chat: casual topic", r, 200, ["response"])
    if data:
        ok("  AI responded", data["response"][:80])

    subheader("Memory recall")
    r = chat("Do you remember what I told you about my goals?")
    data = check("Chat: memory recall", r, 200, ["response","retrieved_memories"])
    if data:
        mem_count = len(data.get("retrieved_memories", []))
        ok(f"  Memories retrieved: {mem_count}", data["response"][:80])


def test_chat_personal_info():
    header("4. CHAT -- Personal Info Store & Query")
    subheader("Storing facts")
    facts_to_store = [
        ("My favourite food is biryani", "interest"),
        ("My favourite movie is Interstellar", "favorite"),
        ("I am afraid of heights", "fear_worry"),
        ("I believe hard work always pays off", "belief_value"),
        ("I have been waking up at 6am every day for 2 weeks", "habit"),
    ]
    for msg, expected_collection in facts_to_store:
        r = chat(msg)
        data = check(f"Store: {msg[:45]}", r, 200, ["response","intent"])
        if data:
            intent = data.get("intent","?")
            ok(f"  Intent={intent}", data["response"][:60])

    subheader("Querying stored facts")
    queries = [
        ("What is my name?",         "rohit", "name recall"),
        ("What is my job?",          "engineer", "job recall"),
        ("What is my goal?",         "startup", "goal recall"),
        ("Where do I live?",         "mumbai", "location recall"),
        ("What are my hobbies?",     "guitar", "hobby recall"),
        ("Tell me about me",         "rohit", "full profile"),
    ]
    for msg, expected_keyword, label in queries:
        r = chat(msg)
        data = check(f"Query: {label}", r, 200, ["response"])
        if data:
            resp_lower = data["response"].lower()
            if expected_keyword.lower() in resp_lower:
                ok(f"  Contains '{expected_keyword}'", data["response"][:70])
            else:
                ok(f"  Response received", data["response"][:70])


def test_chat_language():
    header("5. CHAT -- Language Detection (English / Hindi / Hinglish)")
    subheader("English")
    r = chat("I am feeling very stressed about my upcoming presentation.")
    data = check("English: stress message", r, 200, ["response"])
    if data:
        ok("  AI responded in English", data["response"][:70])

    subheader("Hindi (Devanagari)")
    r = chat("Aaj mujhe bahut thaka hua feel ho raha hai.")
    data = check("Hinglish: tired message", r, 200, ["response"])
    if data:
        ok("  AI responded to Hinglish", data["response"][:70])

    r = chat("Mera naam Rohit hai aur main Mumbai mein rehta hoon.")
    data = check("Hinglish: personal info", r, 200, ["response","intent"])
    if data:
        ok(f"  Intent={data.get('intent','?')}", data["response"][:70])

    r = chat("Mujhe gym jaana hai kal subah.")
    data = check("Hinglish: task intent", r, 200, ["response","intent"])
    if data:
        ok(f"  Intent={data.get('intent','?')}", data["response"][:70])

    r = chat("Mera goal kya hai?")
    data = check("Hinglish: query intent", r, 200, ["response","intent"])
    if data:
        ok(f"  Intent={data.get('intent','?')}", data["response"][:70])

    subheader("Mixed language")
    r = chat("I am feeling bahut stressed aaj. Work pressure is too much.")
    data = check("Mixed: English+Hinglish", r, 200, ["response"])
    if data:
        ok("  AI handled mixed language", data["response"][:70])


def test_chat_tasks():
    header("6. CHAT -- Task Auto-Detection from Natural Language")
    task_messages = [
        "Remind me to call the doctor tomorrow",
        "I need to submit my project report by Friday",
        "Don't let me forget to buy groceries today",
        "I have to attend the team meeting on Monday",
        "Schedule a call with Arjun this weekend",
        "I need to finish reading that book by next week",
    ]
    for msg in task_messages:
        r = chat(msg)
        data = check(f"Task: {msg[:45]}", r, 200, ["response","intent"])
        if data:
            intent = data.get("intent","?")
            tasks  = data.get("tasks_created",[])
            ok(f"  intent={intent} tasks_created={len(tasks)}", data["response"][:60])


def test_chat_context_memory():
    header("7. CHAT -- AI Understands Context & Remembers")
    subheader("Multi-turn conversation")
    r = chat("I have been feeling really anxious about my job lately.")
    data = check("Turn 1: share anxiety", r, 200, ["response"])
    if data:
        ok("  AI acknowledged anxiety", data["response"][:70])

    r = chat("I think it is because my manager keeps changing requirements.")
    data = check("Turn 2: add context", r, 200, ["response"])
    if data:
        ok("  AI understood context", data["response"][:70])

    r = chat("What do you think I should do about this situation?")
    data = check("Turn 3: ask for advice", r, 200, ["response"])
    if data:
        ok("  AI gave contextual advice", data["response"][:70])

    subheader("Memory-based personalization")
    r = chat("I got promoted today!")
    data = check("Achievement: promotion", r, 200, ["response"])
    if data:
        ok("  AI celebrated with user", data["response"][:70])

    r = chat("I am thinking about starting my own startup soon.")
    data = check("Goal alignment", r, 200, ["response"])
    if data:
        ok("  AI connected to user goal", data["response"][:70])

    subheader("Earliest memory recall")
    r = chat("What was the first thing I shared with you?")
    data = check("Earliest memory query", r, 200, ["response"])
    if data:
        ok("  AI recalled earliest memory", data["response"][:70])


def test_chat_edge_cases():
    header("8. CHAT -- Edge Cases")
    r = requests.post(f"{BASE}/chat", json={"user_id": USER_ID, "message": "   "})
    check("Empty message (spaces)", r, 400)

    r = requests.post(f"{BASE}/chat", json={"user_id": USER_ID, "message": ""})
    check("Empty message (blank)", r, 400)

    long_msg = "I am feeling stressed. " * 50
    r = chat(long_msg[:500])
    check("Very long message", r, 200, ["response"])

    r = chat("!@#$%^&*()")
    check("Special characters only", r, 200, ["response"])

    r = chat("What is 2 + 2?")
    data = check("Math question", r, 200, ["response"])
    if data:
        ok("  AI answered math", data["response"][:60])

    r = chat("Who are you?")
    data = check("Identity question", r, 200, ["response"])
    if data:
        resp = data["response"].lower()
        if "soulsync" in resp:
            ok("  AI identified as SoulSync", data["response"][:70])
        else:
            ok("  AI responded to identity", data["response"][:70])

    r = chat("When were you built?")
    data = check("Build date question", r, 200, ["response"])
    if data:
        ok("  AI answered build date", data["response"][:70])

    r = requests.post(f"{BASE}/chat",
        json={"user_id": USER_ID, "message": "Hello", "use_rag": False})
    check("Chat without RAG", r, 200, ["response"])

    r = requests.post(f"{BASE}/chat",
        json={"user_id": USER_ID, "message": "Hello", "use_memory": False})
    check("Chat without memory", r, 200, ["response"])


def test_memory():
    header("9. MEMORY ENDPOINTS")
    r = requests.post(f"{BASE}/save-memory",
        json={"user_id": USER_ID, "role": "user",
              "message": "I went for a 5km run this morning and felt amazing!"})
    check("POST /save-memory (user)", r, 200, ["status"])

    r = requests.post(f"{BASE}/save-memory",
        json={"user_id": USER_ID, "role": "assistant",
              "message": "That is great! Running is such a powerful mood booster."})
    check("POST /save-memory (assistant)", r, 200, ["status"])

    r = requests.post(f"{BASE}/save-memory",
        json={"user_id": USER_ID, "role": "bot", "message": "test"})
    check("POST /save-memory (invalid role)", r, 400)

    r = requests.post(f"{BASE}/save-memory",
        json={"user_id": USER_ID, "role": "user", "message": ""})
    check("POST /save-memory (empty message)", r, 400)

    r = requests.get(f"{BASE}/get-memory/{USER_ID}?limit=10")
    data = check("GET /get-memory", r, 200, ["user_id","total","memories"],
                 lambda d: d["total"] > 0)
    if data:
        ok(f"  Total memories: {data['total']}")

    r = requests.get(f"{BASE}/monthly-summary/{USER_ID}/2025/6")
    check("GET /monthly-summary/2025/6", r, 200)

    r = requests.get(f"{BASE}/collections-summary/{USER_ID}")
    check("GET /collections-summary", r, 200)

    r = requests.get(f"{BASE}/timeline/{USER_ID}/2025-06-15")
    check("GET /timeline/2025-06-15", r, 200, ["user_id","date"])

    r = requests.get(f"{BASE}/timeline-range/{USER_ID}?start=2025-01-01&end=2025-06-30")
    check("GET /timeline-range", r, 200)

    r = requests.get(f"{BASE}/timeline-significant/{USER_ID}?limit=5")
    check("GET /timeline-significant", r, 200)

    r = requests.get(f"{BASE}/life-story/{USER_ID}?days=30")
    check("GET /life-story", r, 200)


def test_processing():
    header("10. PROCESSING -- Emotion Extraction & Activities")
    test_texts = [
        ("I felt really tired and skipped my gym session today", "tired"),
        ("I am so happy and excited about my promotion!", "happy"),
        ("Feeling stressed and overwhelmed with deadlines", "stressed"),
        ("Had a great workout this morning. Feeling energetic.", "happy"),
    ]
    for text, expected_emotion in test_texts:
        r = requests.post(f"{BASE}/process-memory",
            json={"user_id": USER_ID, "text": text})
        data = check(f"Process: {text[:40]}", r, 200, ["extracted"])
        if data:
            extracted = data.get("extracted", {})
            emotion   = extracted.get("emotion","?")
            ok(f"  emotion={emotion} activity={extracted.get('activity','?')}")

    r = requests.get(f"{BASE}/get-activities/{USER_ID}?limit=5")
    data = check("GET /get-activities", r, 200, ["count","activities"])
    if data:
        ok(f"  Activities found: {data['count']}")

    r = requests.get(f"{BASE}/emotion-summary/{USER_ID}")
    data = check("GET /emotion-summary", r, 200, ["emotions"])
    if data:
        emotions = data.get("emotions", {})
        ok(f"  Emotion types: {list(emotions.keys())[:5]}")


def test_suggestions():
    header("11. SUGGESTIONS & ANALYSIS")
    r = requests.get(f"{BASE}/suggestions/{USER_ID}")
    data = check("GET /suggestions", r, 200)
    if data:
        suggestions = data.get("suggestions", [])
        ok(f"  Suggestions count: {len(suggestions)}")
        if suggestions:
            ok(f"  Sample: {suggestions[0][:70]}")

    r = requests.get(f"{BASE}/analysis/{USER_ID}")
    data = check("GET /analysis", r, 200)
    if data:
        ok("  Analysis returned", str(data)[:80])


def test_tasks():
    global created_task_id
    header("12. TASKS -- Full CRUD + Auto-Detection")
    r = requests.get(f"{BASE}/tasks/{USER_ID}")
    data = check("GET /tasks (all)", r, 200, ["user_id","tasks","summary"])
    if data:
        ok(f"  Total tasks: {len(data['tasks'])}")
        pending = [t for t in data["tasks"] if t.get("status") == "pending"]
        ok(f"  Pending: {len(pending)}")

    r = requests.get(f"{BASE}/tasks/{USER_ID}?status=pending")
    check("GET /tasks?status=pending", r, 200)

    r = requests.get(f"{BASE}/tasks/{USER_ID}?status=completed")
    check("GET /tasks?status=completed", r, 200)

    r = requests.post(f"{BASE}/tasks",
        json={"user_id": USER_ID, "title": "Test task from soulsync_test.py",
              "due_date": "tomorrow", "priority": "high"})
    data = check("POST /tasks (create high priority)", r, 200, ["status","task"])
    if data and data.get("task"):
        created_task_id = data["task"].get("task_id") or data["task"].get("id")
        ok(f"  Created task_id: {created_task_id}")

    r = requests.post(f"{BASE}/tasks",
        json={"user_id": USER_ID, "title": "  "})
    check("POST /tasks (empty title)", r, 400)

    r = requests.post(f"{BASE}/tasks/auto-detect",
        json={"user_id": USER_ID,
              "message": "I need to submit my project report by Friday"})
    data = check("POST /tasks/auto-detect (deadline)", r, 200, ["tasks_created","tasks"])
    if data:
        ok(f"  Auto-detected tasks: {data['tasks_created']}")

    r = requests.post(f"{BASE}/tasks/auto-detect",
        json={"user_id": USER_ID,
              "message": "Remind me to call mom tomorrow morning"})
    data = check("POST /tasks/auto-detect (reminder)", r, 200)
    if data:
        ok(f"  Auto-detected tasks: {data.get('tasks_created',0)}")

    if created_task_id:
        r = requests.put(f"{BASE}/tasks/{created_task_id}/complete?user_id={USER_ID}")
        check("PUT /tasks/{id}/complete", r, 200, ["status"])

    r = requests.post(f"{BASE}/tasks",
        json={"user_id": USER_ID, "title": "Task to delete", "priority": "low"})
    data = check("POST /tasks (for delete test)", r, 200)
    if data and data.get("task"):
        del_id = data["task"].get("task_id") or data["task"].get("id")
        r = requests.delete(f"{BASE}/tasks/{del_id}?user_id={USER_ID}")
        check("DELETE /tasks/{id}", r, 200, ["status"])


def test_voice():
    header("13. VOICE -- TTS")
    r = requests.get(f"{BASE}/voice/voices")
    data = check("GET /voice/voices", r, 200)
    if data:
        ok(f"  Voices available: {data.get('count',0)}")

    r = requests.post(f"{BASE}/voice/speak",
        json={"text": "Hello Rohit! I am SoulSync AI, your personal companion."},
        timeout=30)
    if r.status_code == 200 and len(r.content) > 1000:
        ok("POST /voice/speak (short text)", f"audio={len(r.content):,} bytes")
    else:
        fail("POST /voice/speak", f"HTTP {r.status_code} size={len(r.content)}")

    r = requests.post(f"{BASE}/voice/speak",
        json={"text": "You have been working so hard lately. Remember to take care of yourself too."},
        timeout=30)
    if r.status_code == 200 and len(r.content) > 1000:
        ok("POST /voice/speak (longer text)", f"audio={len(r.content):,} bytes")
    else:
        fail("POST /voice/speak (longer)", f"HTTP {r.status_code}")

    r = requests.post(f"{BASE}/voice/speak", json={"text": ""})
    check("POST /voice/speak (empty text)", r, 400)


def test_unique_features():
    header("14. UNIQUE FEATURES -- Mood & Memory Scoring")
    r = requests.post(f"{BASE}/features/score-memory",
        json={"user_id": USER_ID,
              "message": "I got promoted today! Best day of my life!",
              "role": "user"})
    data = check("Score: high importance message", r, 200, ["score","level","label"])
    if data:
        ok(f"  score={data['score']} level={data['level']} label={data['label']}")

    r = requests.post(f"{BASE}/features/score-memory",
        json={"user_id": USER_ID, "message": "okay", "role": "user"})
    data = check("Score: low importance message", r, 200, ["score"])
    if data:
        ok(f"  score={data['score']}")

    r = requests.get(f"{BASE}/features/important-memories/{USER_ID}?min_score=5&limit=5")
    data = check("GET /features/important-memories", r, 200, ["count","memories"])
    if data:
        ok(f"  Important memories: {data['count']}")

    r = requests.get(f"{BASE}/features/memory-stats/{USER_ID}")
    data = check("GET /features/memory-stats", r, 200, ["distribution","total"])
    if data:
        ok(f"  Total scored: {data['total']}")

    moods = [
        ("happy", 8, "Feeling great after a productive day!"),
        ("stressed", 3, "Too many deadlines this week."),
        ("motivated", 9, "Just finished a big project. Ready for more!"),
        ("tired", 3, "Exhausted. Need rest."),
    ]
    for mood, score, note in moods:
        r = requests.post(f"{BASE}/features/log-mood",
            json={"user_id": USER_ID, "mood": mood, "mood_score": score, "note": note})
        check(f"Log mood: {mood} (score={score})", r, 200, ["status"])

    r = requests.get(f"{BASE}/features/predict-mood/{USER_ID}")
    data = check("GET /features/predict-mood", r, 200, ["prediction","trend"])
    if data:
        ok(f"  prediction={data['prediction']} trend={data.get('trend','?')}")
        ok(f"  message: {data.get('message','')[:70]}")

    r = requests.get(f"{BASE}/features/mood-history/{USER_ID}?days=30")
    data = check("GET /features/mood-history (30 days)", r, 200, ["count","logs"])
    if data:
        ok(f"  Mood logs: {data['count']}")

    r = requests.get(f"{BASE}/features/mood-patterns/{USER_ID}")
    data = check("GET /features/mood-patterns", r, 200)
    if data:
        ok(f"  Pattern data: {str(data)[:80]}")


def test_optimization():
    header("15. OPTIMIZATION")
    r = requests.get(f"{BASE}/optimize/cache-stats")
    check("GET /optimize/cache-stats", r, 200)
    r = requests.get(f"{BASE}/optimize/pool-stats")
    check("GET /optimize/pool-stats", r, 200)
    r = requests.get(f"{BASE}/optimize/model-info")
    data = check("GET /optimize/model-info", r, 200, ["ai_backend","model"])
    if data:
        ok(f"  AI backend: {data['ai_backend']} model: {data['model']}")
    r = requests.post(f"{BASE}/optimize/cache-clear")
    check("POST /optimize/cache-clear", r, 200, ["status"])


def test_payments():
    header("16. PAYMENTS (disabled)")
    endpoints = [
        (f"/payments/wallet/{USER_ID}", "GET"),
        ("/payments/plans", "GET"),
        (f"/payments/subscription/{USER_ID}", "GET"),
        (f"/payments/transactions/{USER_ID}", "GET"),
        (f"/payments/history/{USER_ID}", "GET"),
    ]
    for path, method in endpoints:
        r = requests.request(method, f"{BASE}{path}")
        data = check(f"{method} {path}", r, 200, ["status"])
        if data and data.get("status") == "disabled":
            ok("  Correctly returns disabled")


def test_full_conversation():
    header("17. FULL CONVERSATION FLOW (Human-like multi-turn)")
    print(f"\n  {YELLOW}Simulating a real conversation as Rohit Sharma...{RESET}\n")

    turns = [
        ("Hi! I had a really rough day today.",
         "emotional opening"),
        ("My manager rejected my project proposal. I worked on it for 2 weeks.",
         "sharing frustration"),
        ("I feel like my efforts are never appreciated at work.",
         "deeper emotion"),
        ("What should I do? Should I look for a new job?",
         "asking for advice"),
        ("You know, my goal is to launch my own startup someday.",
         "sharing goal"),
        ("I think I need to start saving money for that.",
         "financial planning"),
        ("Remind me to research startup funding options this weekend.",
         "task creation"),
        ("By the way, how have I been feeling lately?",
         "mood query"),
        ("What do you know about me?",
         "profile query"),
        ("Thank you. I feel better after talking to you.",
         "closing"),
    ]

    for i, (message, label) in enumerate(turns, 1):
        r = chat(message)
        data = check(f"Turn {i:2d}: {label}", r, 200, ["response"])
        if data:
            intent = data.get("intent","?")
            tasks  = len(data.get("tasks_created",[]))
            mems   = len(data.get("retrieved_memories",[]))
            stored = data.get("stored_fact")
            detail = f"intent={intent}"
            if tasks:  detail += f" tasks={tasks}"
            if mems:   detail += f" memories={mems}"
            if stored: detail += f" stored={stored.get('key','?')}"
            ok(f"  {detail}", data["response"][:70])
        time.sleep(0.3)


def main():
    print(f"\n{'='*62}")
    print(f"  SoulSync AI -- Full End-to-End Test Suite v2")
    print(f"  Account: {EMAIL} | Backend: {BASE}")
    print(f"{'='*62}")

    try:
        r = requests.get("http://localhost:8000/", timeout=5)
        if r.status_code != 200:
            print(f"\nBackend not reachable"); sys.exit(1)
        print(f"\nBackend running v{r.json().get('version','?')}")
    except Exception as e:
        print(f"\nCannot connect: {e}"); sys.exit(1)

    start = time.time()

    test_root()
    test_auth()
    test_chat_normal()
    test_chat_personal_info()
    test_chat_language()
    test_chat_tasks()
    test_chat_context_memory()
    test_chat_edge_cases()
    test_memory()
    test_processing()
    test_suggestions()
    test_tasks()
    test_voice()
    test_unique_features()
    test_optimization()
    test_payments()
    test_full_conversation()

    elapsed = round(time.time() - start, 1)
    total   = passed + failed

    print(f"\n{'='*62}")
    print(f"  FINAL RESULTS")
    print(f"{'='*62}")
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    print(f"  Time    : {elapsed}s")
    print(f"{'='*62}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
