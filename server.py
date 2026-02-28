import os
os.environ['MUJOCO_GL'] = 'disabled'

import mujoco
import numpy as np
import asyncio
import json
import websockets
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

XML = """
<mujoco model="hugo">
  <option timestep="0.005" gravity="0 0 -9.81"/>
  <default>
    <joint damping="0.5" armature="0.01"/>
    <geom condim="3" friction="0.8 0.1 0.1"/>
    <motor ctrllimited="true" ctrlrange="-2.5 2.5"/>
  </default>
  <worldbody>
    <light pos="0 0 4" dir="0 0 -1" diffuse="1 1 1"/>
    <geom name="floor" type="plane" size="20 20 .1" rgba=".9 .9 .9 1" condim="3"/>
    <!-- Dorm room collision (matches dorm_v2: room 3.86x5.76m, Three x=right y=up z=back → MuJoCo x=-z y=-x z=y) -->
    <geom name="wall_back" type="box" size="0.05 1.93 1.41" pos="2.88 0 1.41" rgba=".7 .7 .7 .3"/>
    <geom name="wall_front" type="box" size="0.05 1.93 1.41" pos="-2.88 0 1.41" rgba=".7 .7 .7 .3"/>
    <geom name="wall_left" type="box" size="2.88 0.05 1.41" pos="0 1.93 1.41" rgba=".7 .7 .7 .3"/>
    <geom name="wall_right" type="box" size="2.88 0.05 1.41" pos="0 -1.93 1.41" rgba=".7 .7 .7 .3"/>
    <!-- Beds: right bed center (0,0,-2.3) Three → MuJoCo (2.3,0,0.15); left bed (1.4,0,-1) Three → MuJoCo (1,-1.4,0.15) -->
    <geom name="bed_right" type="box" size="1.9 0.5 0.13" pos="2.3 0 0.15" rgba=".2 .2 .4 .5"/>
    <geom name="bed_left" type="box" size="0.5 1.8 0.13" pos="1.0 -1.4 0.15" rgba=".2 .2 .4 .5"/>
    <!-- Desk/wardrobe: desk (1.93,0.4,0.5) Three → MuJoCo (-0.5,-1.93,0.4); wardrobe left of desk -->
    <geom name="desk" type="box" size="0.35 0.31 0.4" pos="-0.5 -1.6 0.4" rgba=".6 .5 .3 .5"/>
    <geom name="wardrobe" type="box" size="0.3 0.3 1.0" pos="-0.9 -1.6 1.0" rgba=".6 .5 .3 .5"/>
    <geom name="dresser" type="box" size="0.38 0.25 0.43" pos="-0.5 1.7 0.43" rgba=".6 .5 .3 .5"/>
    <body name="torso" pos="0 0 1.4">
      <freejoint name="root"/>
      <geom name="torso_geom" type="capsule" size="0.07" fromto="0 -.07 0 0 .07 0" mass="5"/>
      <body name="head" pos="0 0 .22">
        <geom type="sphere" size=".09" mass="2"/>
      </body>
      <body name="lthigh" pos="0 -.1 -.04">
        <joint name="lhip_x" type="hinge" axis="1 0 0" range="-60 90" damping="2"/>
        <joint name="lhip_y" type="hinge" axis="0 1 0" range="-30 30" damping="1"/>
        <joint name="lhip_z" type="hinge" axis="0 0 1" range="-30 30" damping="1"/>
        <geom type="capsule" size="0.06" fromto="0 0 0 0 0 -.34" mass="4"/>
        <body name="lshin" pos="0 0 -.38">
          <joint name="lknee" type="hinge" axis="0 1 0" range="-160 -2" damping="2"/>
          <geom type="capsule" size="0.049" fromto="0 0 0 0 0 -.3" mass="3"/>
          <body name="lfoot" pos="0 0 -.33">
            <joint name="lankle" type="hinge" axis="0 1 0" range="-40 40" damping="1"/>
            <geom type="capsule" size="0.04" fromto="-.05 0 0 .1 0 0" mass="1"/>
          </body>
        </body>
      </body>
      <body name="rthigh" pos="0 .1 -.04">
        <joint name="rhip_x" type="hinge" axis="1 0 0" range="-60 90" damping="2"/>
        <joint name="rhip_y" type="hinge" axis="0 1 0" range="-30 30" damping="1"/>
        <joint name="rhip_z" type="hinge" axis="0 0 1" range="-30 30" damping="1"/>
        <geom type="capsule" size="0.06" fromto="0 0 0 0 0 -.34" mass="4"/>
        <body name="rshin" pos="0 0 -.38">
          <joint name="rknee" type="hinge" axis="0 1 0" range="-160 -2" damping="2"/>
          <geom type="capsule" size="0.049" fromto="0 0 0 0 0 -.3" mass="3"/>
          <body name="rfoot" pos="0 0 -.33">
            <joint name="rankle" type="hinge" axis="0 1 0" range="-40 40" damping="1"/>
            <geom type="capsule" size="0.04" fromto="-.05 0 0 .1 0 0" mass="1"/>
          </body>
        </body>
      </body>
      <body name="luarm" pos="0 -.18 .06">
        <joint name="lshoulder" type="ball" damping="1"/>
        <geom type="capsule" size="0.04" fromto="0 0 0 0 0 -.25" mass="2"/>
        <body name="lfarm" pos="0 0 -.28">
          <joint name="lelbow" type="hinge" axis="0 1 0" range="-140 0" damping="1"/>
          <geom type="capsule" size="0.035" fromto="0 0 0 0 0 -.22" mass="1.5"/>
        </body>
      </body>
      <body name="ruarm" pos="0 .18 .06">
        <joint name="rshoulder" type="ball" damping="1"/>
        <geom type="capsule" size="0.04" fromto="0 0 0 0 0 -.25" mass="2"/>
        <body name="rfarm" pos="0 0 -.28">
          <joint name="relbow" type="hinge" axis="0 1 0" range="-140 0" damping="1"/>
          <geom type="capsule" size="0.035" fromto="0 0 0 0 0 -.22" mass="1.5"/>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <!-- Hip motors (3 dof each leg) -->
    <motor name="act_lhip_x" joint="lhip_x" gear="35"/>
    <motor name="act_lhip_y" joint="lhip_y" gear="25"/>
    <motor name="act_lhip_z" joint="lhip_z" gear="25"/>
    <motor name="act_rhip_x" joint="rhip_x" gear="35"/>
    <motor name="act_rhip_y" joint="rhip_y" gear="25"/>
    <motor name="act_rhip_z" joint="rhip_z" gear="25"/>
    <!-- Knees + ankles -->
    <motor name="act_lknee"  joint="lknee"  gear="45"/>
    <motor name="act_lankle" joint="lankle" gear="20"/>
    <motor name="act_rknee"  joint="rknee"  gear="45"/>
    <motor name="act_rankle" joint="rankle" gear="20"/>
  </actuator>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(XML)
data  = mujoco.MjData(model)

# Add small perturbation so it falls interestingly
data.qvel[3] = 0.3
data.qvel[5] = 0.2

clients = set()

# Latest locomotion command (shared). Client sends:
# {"type":"locomotion","vx":0,"vz":-1,"speed":1,"yaw":0,"phase":...}
latest_cmd = {
    "vx": 0.0,
    "vz": 0.0,
    "speed": 0.0,
    "yaw": 0.0,
    "phase": 0.0,
}
latest_lock = threading.Lock()

async def handler(ws):
    clients.add(ws)
    print(f"Client connected ({len(clients)} total)")
    try:
        async for msg in ws:
            try:
                if msg == "t":
                    continue
                d = json.loads(msg)
                if isinstance(d, dict) and d.get("type") == "locomotion":
                    with latest_lock:
                        latest_cmd["vx"] = float(d.get("vx", 0.0))
                        latest_cmd["vz"] = float(d.get("vz", 0.0))
                        latest_cmd["speed"] = float(d.get("speed", 0.0))
                        latest_cmd["yaw"] = float(d.get("yaw", 0.0))
                        latest_cmd["phase"] = float(d.get("phase", latest_cmd["phase"]))
            except Exception:
                pass
    finally:
        clients.discard(ws)
        print("Client disconnected")

async def physics_loop():
    mujoco.mj_resetData(model, data)
    data.qvel[3] = 0.3
    data.qvel[5] = 0.2
    step = 0
    # Cache joint / actuator indices for fast access
    def jadr(name: str):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        return int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid])

    joint_addrs = {
        "lhip_x": jadr("lhip_x"),
        "lhip_y": jadr("lhip_y"),
        "lhip_z": jadr("lhip_z"),
        "lknee":  jadr("lknee"),
        "lankle": jadr("lankle"),
        "rhip_x": jadr("rhip_x"),
        "rhip_y": jadr("rhip_y"),
        "rhip_z": jadr("rhip_z"),
        "rknee":  jadr("rknee"),
        "rankle": jadr("rankle"),
    }

    act_names = [
        "act_lhip_x","act_lhip_y","act_lhip_z","act_rhip_x","act_rhip_y","act_rhip_z",
        "act_lknee","act_lankle","act_rknee","act_rankle",
    ]
    act_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in act_names]

    def getq(name: str):
        qa, va = joint_addrs[name]
        return float(data.qpos[qa]), float(data.qvel[va])

    def setctrl(act_i: int, u: float):
        # ctrl is in actuator order; act_i is actuator id
        data.ctrl[act_i] = np.clip(u, -2.5, 2.5)

    # Simple PD + gait: not "smart", but enough to visibly walk/translate under physics.
    KP_HIP = 8.0
    KD_HIP = 1.2
    KP_KNEE = 10.0
    KD_KNEE = 1.5
    KP_ANK = 4.0
    KD_ANK = 0.8

    while True:
        # Read latest locomotion intent
        with latest_lock:
            vx = float(latest_cmd["vx"])
            vz = float(latest_cmd["vz"])
            spd = float(latest_cmd["speed"])
            phase = float(latest_cmd["phase"])

        # Update phase locally too (in case client doesn't send)
        if spd > 0.0:
            phase += 0.05 * (1.0 + 0.6 * min(spd, 2.0))
            with latest_lock:
                latest_cmd["phase"] = phase

        # Target angles (radians). We use phase to swing thighs, bend knees.
        swing = np.sin(phase)
        swing2 = np.sin(phase + np.pi)
        # Move direction affects posture amplitude a bit
        mag = float(np.clip(np.hypot(vx, vz), 0.0, 1.0))
        amp = (0.35 + 0.35 * mag) * (1.0 if spd > 0 else 0.0)

        # Desired joint targets
        tgt = {
            "lhip_x":  0.25 * amp + 0.55 * amp * swing,
            "rhip_x":  0.25 * amp + 0.55 * amp * swing2,
            "lhip_y":  0.0,
            "rhip_y":  0.0,
            "lhip_z":  0.08 * amp * (-swing),
            "rhip_z":  0.08 * amp * (-swing2),
            "lknee":  -0.35 * amp * max(0.0, -swing),
            "rknee":  -0.35 * amp * max(0.0, -swing2),
            "lankle":  0.12 * amp * max(0.0, -swing),
            "rankle":  0.12 * amp * max(0.0, -swing2),
        }

        # PD compute torques
        def pd(name: str, kp: float, kd: float):
            q, qd = getq(name)
            return kp * (tgt[name] - q) - kd * qd

        # Apply to actuators (by actuator id)
        # hips
        setctrl(act_ids[0], pd("lhip_x", KP_HIP, KD_HIP))
        setctrl(act_ids[1], pd("lhip_y", KP_HIP, KD_HIP))
        setctrl(act_ids[2], pd("lhip_z", KP_HIP, KD_HIP))
        setctrl(act_ids[3], pd("rhip_x", KP_HIP, KD_HIP))
        setctrl(act_ids[4], pd("rhip_y", KP_HIP, KD_HIP))
        setctrl(act_ids[5], pd("rhip_z", KP_HIP, KD_HIP))
        # knees/ankles
        setctrl(act_ids[6], pd("lknee",  KP_KNEE, KD_KNEE))
        setctrl(act_ids[7], pd("lankle", KP_ANK,  KD_ANK))
        setctrl(act_ids[8], pd("rknee",  KP_KNEE, KD_KNEE))
        setctrl(act_ids[9], pd("rankle", KP_ANK,  KD_ANK))

        for _ in range(4):
            mujoco.mj_step(model, data)
        step += 1

        if clients:
            # qpos layout:
            # 0-2: root xyz
            # 3-6: root quat (w,x,y,z)
            # 7:  lhip_x, 8: lhip_y, 9: lhip_z
            # 10: lknee
            # 11: lankle
            # 12: rhip_x, 13: rhip_y, 14: rhip_z
            # 15: rknee
            # 16: rankle
            # 17-19: lshoulder (ball)
            # 20: lelbow
            # 21-23: rshoulder (ball)
            # 24: relbow

            q = data.qpos
            state = {
                "step": step,
                "pos":    q[0:3].tolist(),
                "quat":   q[3:7].tolist(),
                "lhip":   q[7:10].tolist(),
                "lknee":  float(q[10]),
                "lankle": float(q[11]),
                "rhip":   q[12:15].tolist(),
                "rknee":  float(q[15]),
                "rankle": float(q[16]),
                "lshoulder": q[17:20].tolist() if len(q) > 19 else [0,0,0],
                "lelbow":    float(q[20]) if len(q) > 20 else 0,
                "rshoulder": q[21:24].tolist() if len(q) > 23 else [0,0,0],
                "relbow":    float(q[24]) if len(q) > 24 else 0,
                "height": float(q[2]),
                "contacts": int(data.ncon)
            }
            msg = json.dumps(state)
            dead = set()
            for c in clients:
                try:
                    await c.send(msg)
                except:
                    dead.add(c)
            clients -= dead

        if step % 100 == 0:
            print(f"Step {step} | height {data.qpos[2]:.3f} | contacts {data.ncon}")

        await asyncio.sleep(0.016)

# Serve the HTML file too
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def serve_html():
    httpd = HTTPServer(('localhost', 8766), Handler)
    print("HTML server: http://localhost:8766")
    httpd.serve_forever()

threading.Thread(target=serve_html, daemon=True).start()

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("="*40)
        print("Physics server: ws://localhost:8765")
        print("Open browser:   http://localhost:8766")
        print("="*40)
        await physics_loop()

import nest_asyncio
nest_asyncio.apply()
asyncio.get_event_loop().run_until_complete(main())