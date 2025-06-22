import os
import subprocess
import config
MODULE_CONFIG = {
    "name": "ffmpeg",
    "libraries": [
        "libavcodec",
        "libavformat",
        "libavutil",
        "libswresample",
        "libswscale",
        "libavdevice",
    ],
    "repo": "https://github.com/FFmpeg/FFmpeg.git",
    "repo_env": "REPO_FFMPEG",
    "repo_save_dir": "FFmpeg"
}

def wait_proc(proc:subprocess.Popen):
  sto, ste = proc.communicate()
  if proc.returncode != 0 :
    print(f"Error output:\n{ste}")
    return False
  return True


def detect_openssl():
  pass


def build_repo_android(source_path: str, install_prefix: str, toolchain_vars: dict, force_re_compile: bool = False):
    if not os.path.exists(source_path):
        raise IOError(f"Can not find source {source_path}, clone first!")
    old_wk_dir = os.getcwd()
    os.chdir(source_path)
    try:
        # 复制当前环境变量并添加 toolchain_vars 中的变量
        env = os.environ.copy()
        env.update(toolchain_vars)
        if not os.path.exists("config.h") or force_re_compile:
          # 构建命令参数
          cfg_flags = config.configs
          triple_cc = env.get('TRIPLE_CC', '')
          ar = env.get('AR', '')
          nm = env.get('NM', '')
          strip = env.get('STRIP', '')
          ranlib = env.get('RANLIB', '')
          c_flags = env.get('C_FLAGS', '')
          ldflags = env.get('LDFLAGS', '')
          mr_pkg_config_executable = env.get('PKG_CONFIG_EXECUTABLE', '')

          command = [
              './configure',
              *cfg_flags, # * 是解包操作符，会把序列容器中的元素解出来
              f'--cc={triple_cc}',
              f'--as={triple_cc}',
              f'--ld={triple_cc}',
              f'--ar={ar}',
              f'--nm={nm}',
              f'--strip={strip}',
              f'--ranlib={ranlib}',
              f'--extra-cflags={c_flags}',
              f'--extra-cxxflags={c_flags}',
              f'--extra-ldflags={ldflags}',
              f'--pkg-config={mr_pkg_config_executable}'
              f'--prefix={install_prefix}'
          ]

          # 启动子进程
          process = subprocess.Popen(
              command,
              env=env,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
              text=True
          )
          if not wait_proc(process):
            raise SystemError(f"Configure {source_path} has failed!")
        proc=subprocess.Popen(["make V=1", "-j8"], env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)
        if not wait_proc(proc):
          raise SystemError(f"Make failed!")
        
    except Exception as e:
      print(f"An error occurred: {e}")
      raise
    finally:
      os.chdir(old_wk_dir)