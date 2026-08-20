import requests, json

BASE = "http://localhost:8000"


def send(sid, msg):
    r = requests.post(f"{BASE}/api/chat", json={"session_id": sid, "message": msg}, timeout=5)
    d = r.json()
    print(f">> {msg}\n<< {d['reply']}\n")
    return d


def analytics(sid):
    a = requests.get(f"{BASE}/api/analytics/{sid}", timeout=5).json()
    print("ANALYTICS:", json.dumps(a, indent=2, ensure_ascii=False))


print("### TC1: Hinglish, config capture + successful booking ###")
d = send(None, "Namaste")
sid = d["session_id"]
send(sid, "Mujhe 3 BHK chahiye, price kya hai?")
send(sid, "Ok theek hai, site visit karna hai")
send(sid, "25 August")
send(sid, "Afternoon 3 baje")
send(sid, "Rohit Sharma")
send(sid, "9876543210")
analytics(sid)

print("\n### TC2: Booking FAILURE (9 am slot unavailable) ###")
d = send(None, "Hi I want a 2 BHK")
sid2 = d["session_id"]
send(sid2, "site visit please")
send(sid2, "28 August")
send(sid2, "9 am")
send(sid2, "Priya Verma")
d = send(sid2, "9123456780")
print("ended:", d["ended"])
analytics(sid2)

print("\n### TC3: Price objection ###")
d = send(None, "Hello")
sid3 = d["session_id"]
d = send(sid3, "3 BHK is too expensive for me")
analytics(sid3)

print("\n### TC4: Unknown question (possession date) ###")
d = send(None, "Hi")
sid4 = d["session_id"]
d = send(sid4, "What is the possession date?")
analytics(sid4)

print("\n### TC5: Busy customer -> call later ###")
d = send(None, "Hello")
sid5 = d["session_id"]
d = send(sid5, "I'm busy right now")
d = send(sid5, "call me tomorrow evening")
analytics(sid5)

print("\n### TC6: Hard stop / do-not-contact ###")
d = send(None, "Hi")
sid6 = d["session_id"]
d = send(sid6, "Please stop contacting me, remove my number")
print("ended:", d["ended"])
analytics(sid6)

print("\n### TC7: Human escalation request ###")
d = send(None, "Hi")
sid7 = d["session_id"]
d = send(sid7, "I want to talk to a human manager")
analytics(sid7)
