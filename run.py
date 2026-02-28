import sys
print("Python running")

try:
    import mujoco
    print("mujoco version:", mujoco.__version__)
except Exception as e:
    print("mujoco failed:", e)
    sys.exit()

m = mujoco.MjModel.from_xml_string("<mujoco><worldbody><body><freejoint/><geom type='sphere' size='.1' mass='1'/></body></worldbody></mujoco>")
d = mujoco.MjData(m)

for i in range(100):
    mujoco.mj_step(m, d)

print("height after 100 steps:", round(d.qpos[2], 4))
print("DONE")
