import asyncio, json, math, random, time, os
from aiohttp import web, WSMsgType

ROOT=os.path.dirname(os.path.abspath(__file__))
players={}; sockets={}; zombies={}; loot={}; profiles={}; next_id=0
OUTPOSTS=[(0,0,13),(105,-75,12)]
random.seed(37)
for i in range(55):
 x=random.uniform(-175,175);z=random.uniform(-175,175)
 if any(math.hypot(x-a,z-b)<r+9 for a,b,r in OUTPOSTS):continue
 zombies[str(i)]={'id':str(i),'x':x,'z':z,'hp':100,'alive':True,'respawn':0}
for i in range(85):
 x=random.uniform(-180,180);z=random.uniform(-180,180)
 if any(math.hypot(x-a,z-b)<r for a,b,r in OUTPOSTS):continue
 loot[str(i)]={'id':str(i),'x':x,'z':z,'kind':random.choices(['scrap','ammo','medkit','food','rare'],[45,25,15,12,3])[0]}

def safe(x,z):return any(math.hypot(x-a,z-b)<r for a,b,r in OUTPOSTS)
def state():return {'type':'state','players':list(players.values()),'zombies':[z for z in zombies.values() if z['alive']],'loot':list(loot.values()),'outposts':OUTPOSTS}
async def send(ws,data):
 try:await ws.send_json(data)
 except Exception:pass
async def broadcast(data):
 for ws in list(sockets.values()):await send(ws,data)

async def websocket(request):
 global next_id
 ws=web.WebSocketResponse(heartbeat=20);await ws.prepare(request)
 next_id+=1;pid=str(next_id);name='Survivor'+pid
 players[pid]={'id':pid,'name':name,'x':0,'z':0,'yaw':0,'hp':100,'money':0,'kills':0,'inventory':{'ammo':60,'medkit':2,'food':2,'scrap':0,'rare':0},'lastShot':0}
 sockets[pid]=ws
 await send(ws,{'type':'welcome','id':pid,'world':state()})
 await broadcast({'type':'joined','player':players[pid]})
 try:
  async for msg in ws:
   if msg.type!=WSMsgType.TEXT:continue
   try:d=json.loads(msg.data)
   except Exception:continue
   p=players.get(pid)
   if not p:continue
   typ=d.get('type')
   if typ=='name':p['name']=str(d.get('name','Survivor'))[:20].strip() or 'Survivor'
   elif typ=='move':
    x=float(d.get('x',p['x']));z=float(d.get('z',p['z']))
    if math.isfinite(x) and math.isfinite(z) and abs(x)<195 and abs(z)<195 and math.hypot(x-p['x'],z-p['z'])<12:
     p['x']=x;p['z']=z;p['yaw']=float(d.get('yaw',0))
   elif typ=='shoot':
    now=time.monotonic()
    if now-p['lastShot']<.24 or p['inventory']['ammo']<=0 or p['hp']<=0:continue
    p['lastShot']=now;p['inventory']['ammo']-=1
    zid=str(d.get('target',''));z=zombies.get(zid)
    if z and z['alive'] and not safe(z['x'],z['z']) and math.hypot(z['x']-p['x'],z['z']-p['z'])<45:
     z['hp']-=35
     if z['hp']<=0:
      z['alive']=False;z['respawn']=now+22;p['kills']+=1;p['money']+=150
      await broadcast({'type':'kill','id':zid,'by':pid})
    await send(ws,{'type':'profile','player':p})
   elif typ=='pickup':
    item=loot.get(str(d.get('id','')))
    if item and math.hypot(item['x']-p['x'],item['z']-p['z'])<4:
     k=item['kind'];p['inventory'][k]+= (20 if k=='ammo' else 1);loot.pop(item['id'],None)
     if k=='scrap':p['money']+=25
     await broadcast({'type':'lootgone','id':item['id']});await send(ws,{'type':'profile','player':p})
   elif typ=='heal':
    if p['inventory']['medkit']>0 and p['hp']<100:p['inventory']['medkit']-=1;p['hp']=min(100,p['hp']+60);await send(ws,{'type':'profile','player':p})
   elif typ=='chat':
    message=str(d.get('message',''))[:160].strip()
    if message.lower()=='westonmerk':
     # Prototype cheat is not account-authenticated; restrict to server-designated owner username.
     if p['name'].lower()=='moose1354':p['money']+=100000000;await send(ws,{'type':'system','message':'Owner reward: +$100,000,000'});await send(ws,{'type':'profile','player':p})
     else:await send(ws,{'type':'system','message':'This code is restricted to the server owner.'})
    elif message:await broadcast({'type':'chat','name':p['name'],'message':message})
 except Exception as e:print('client error',e)
 finally:
  players.pop(pid,None);sockets.pop(pid,None);await broadcast({'type':'left','id':pid})
 return ws

async def tick(app):
 try:
  t=0
  while True:
   await asyncio.sleep(.12);t+=1;now=time.monotonic()
   for z in zombies.values():
    if not z['alive']:
     if now>z['respawn']:z['alive']=True;z['hp']=100
     continue
    if safe(z['x'],z['z']):z['x']+=5;z['z']+=5;continue
    nearest=None;dist=1e9
    for p in players.values():
     if p['hp']<=0 or safe(p['x'],p['z']):continue
     d=math.hypot(p['x']-z['x'],p['z']-z['z'])
     if d<dist:dist=d;nearest=p
    if nearest and dist<32:
     if dist>1.7:
      speed=.23;nx=z['x']+(nearest['x']-z['x'])/dist*speed;nz=z['z']+(nearest['z']-z['z'])/dist*speed
      if not safe(nx,nz):z['x']=nx;z['z']=nz
     elif t%9==0:
      nearest['hp']=max(0,nearest['hp']-8)
      if nearest['hp']==0:nearest['x']=0;nearest['z']=0;nearest['hp']=100
      await send(sockets[nearest['id']],{'type':'profile','player':nearest})
   if t%2==0:await broadcast(state())
 except asyncio.CancelledError:pass

async def startup(app):app['task']=asyncio.create_task(tick(app))
async def cleanup(app):app['task'].cancel();await asyncio.gather(app['task'],return_exceptions=True)
app=web.Application();app.router.add_get('/ws',websocket);app.router.add_static('/',os.path.join(ROOT,'public'),show_index=True);app.on_startup.append(startup);app.on_cleanup.append(cleanup)
if __name__=='__main__':web.run_app(app,host='0.0.0.0',port=int(os.getenv('PORT','8080')))
