import sys
import os
import platform
import types
import ctypes

if platform.system() == "Darwin":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    pixi_lib_path = os.path.abspath("../../.pixi/envs/default/lib")
    if os.path.exists(pixi_lib_path):
        os.environ['DYLD_LIBRARY_PATH'] = pixi_lib_path + (":" + os.environ.get('DYLD_LIBRARY_PATH', '') if os.environ.get('DYLD_LIBRARY_PATH') else "")

    m = types.ModuleType('unitree_sdk2py.utils.timerfd')
    m.timerfd_create = lambda x, y: 0
    m.timerfd_settime = lambda a, b, c, d: 0
    m.timerfd_gettime = lambda a, b: 0
    class timespec(ctypes.Structure):
        _fields_ = [("sec", ctypes.c_long), ("nsec", ctypes.c_long)]
    class itimerspec(ctypes.Structure):
        _fields_ = [("interval", timespec), ("value", timespec)]
        @classmethod
        def from_seconds(cls, interval, value):
            return cls()
    m.timespec = timespec
    m.itimerspec = itimerspec
    sys.modules['unitree_sdk2py.utils.timerfd'] = m

    import unitree_sdk2py.utils.thread as thread_mod
    def patched_LoopFunc(self):
        import time
        while not getattr(self, '_RecurrentThread__quit'):
            try:
                target = getattr(self, '_RecurrentThread__loopTarget')
                args = getattr(self, '_RecurrentThread__loopArgs')
                kwargs = getattr(self, '_RecurrentThread__loopKwargs')
                target(*args, **kwargs)
            except Exception as e:
                print(f"[RecurrentThread Patch] Error in target: {e}")
            time.sleep(getattr(self, '_RecurrentThread__inter'))
            
    thread_mod.RecurrentThread._RecurrentThread__LoopFunc = patched_LoopFunc


import time
import mujoco
import mujoco.viewer
from threading import Thread
import threading

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py_bridge import UnitreeSdk2Bridge, ElasticBand

import config


locker = threading.Lock()

mj_model = mujoco.MjModel.from_xml_path(config.ROBOT_SCENE)
mj_data = mujoco.MjData(mj_model)


if config.ENABLE_ELASTIC_BAND:
    elastic_band = ElasticBand()
    if config.ROBOT == "h1" or config.ROBOT == "g1":
        band_attached_link = mj_model.body("torso_link").id
    else:
        band_attached_link = mj_model.body("base_link").id
    viewer = mujoco.viewer.launch_passive(
        mj_model, mj_data, key_callback=elastic_band.MujuocoKeyCallback
    )
else:
    viewer = mujoco.viewer.launch_passive(mj_model, mj_data)

mj_model.opt.timestep = config.SIMULATE_DT
num_motor_ = mj_model.nu
dim_motor_sensor_ = 3 * num_motor_

time.sleep(0.2)


def SimulationThread():
    global mj_data, mj_model

    ChannelFactoryInitialize(config.DOMAIN_ID, config.INTERFACE)
    unitree = UnitreeSdk2Bridge(mj_model, mj_data)

    if config.USE_JOYSTICK:
        unitree.SetupJoystick(device_id=0, js_type=config.JOYSTICK_TYPE)
    if config.PRINT_SCENE_INFORMATION:
        unitree.PrintSceneInformation()

    while viewer.is_running():
        step_start = time.perf_counter()

        locker.acquire()

        if config.ENABLE_ELASTIC_BAND:
            if elastic_band.enable:
                mj_data.xfrc_applied[band_attached_link, :3] = elastic_band.Advance(
                    mj_data.qpos[:3], mj_data.qvel[:3]
                )
        mujoco.mj_step(mj_model, mj_data)

        locker.release()

        time_until_next_step = mj_model.opt.timestep - (
            time.perf_counter() - step_start
        )
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)


def PhysicsViewerThread():
    while viewer.is_running():
        locker.acquire()
        viewer.sync()
        locker.release()
        time.sleep(config.VIEWER_DT)


if __name__ == "__main__":
    viewer_thread = Thread(target=PhysicsViewerThread)
    sim_thread = Thread(target=SimulationThread)

    viewer_thread.start()
    sim_thread.start()
