import argparse
import logging
import base
import os
import module_ffmpeg

def setup_loggers(logger_path:str):
  logger = logging.getLogger('build')
  logger.setLevel(logging.DEBUG)

  # 创建一个文件处理程序，将日志写入到文件
  file_handler = logging.FileHandler(logger_path)
  file_handler.setLevel(logging.DEBUG)

  # 创建一个控制台处理程序，将日志输出到stdout
  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging.DEBUG)

  # 定义日志格式
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_handler.setFormatter(formatter)
  console_handler.setFormatter(formatter)

  # 将处理程序添加到logger实例中
  logger.addHandler(file_handler)
  logger.addHandler(console_handler)
  return logger


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--platform', type=str, default='android', choices=['apple', 'android', 'ios', 'tvos', 'macos', 'all'], help='platform must be: [apple|android|ios|tvos|macos|all]')
    # only avalibale for apple
    parser.add_argument('-a', '--arch', type=str, default='arm64', choices=['arm64', 'arm64-simulator','x86_64', 'x86_64-simulator', 'all'], help='arch must be: [arm64|arm64-simulator|x86_64|x86_64-simulator|all], only avaliable for apple')
    parser.add_argument('-w', '--workspace', type=str, default='build', help='specify workspace')
    parser.add_argument('--prefix', type=str, help='install the library')
    parser.add_argument('--action',  type=str, default='init', choices=['init', 'build', 'install'], help='action must be: [init|build|install]')
    parser.add_argument('--library', type=str, default="", help='specify the library name')
    # parser.add_argument('--install', action='store_true', help='install the library')
    # # prepare the repo, clone the sample code, and don't build it.
    # parser.add_argument('--init', action='store_true', help='initialize the library')
    # parser.add_argument('--build', action='store_true', help='build the library')

    args = parser.parse_args()
    return args
  
def preapre_workspaces(bcfg:base.BuildConfigure):
  if not bcfg.action == "init":
    logger.info("Not initialize the library, skip checking workspace!")
    return
  bcfg.prepare()
  
if __name__ == "__main__":
  args = parse_args()
  logger = setup_loggers("build.log")
  build_cfg = base.BuildConfigure(args.platform, args.arch, args.workspace, args.prefix, args.action)
  toolchain_vars, host_vars = base.get_platform_envs(build_cfg)
  preapre_workspaces(build_cfg)

  ffmpeg_module = module_ffmpeg.FFMpegModule(build_cfg, toolchain_vars, host_vars)
    #   "repo": "https://github.com/FFmpeg/FFmpeg.git",
    # "repo_env": "REPO_FFMPEG",
    # "repo_save_dir": "FFmpeg"
  ffconfig=ffmpeg_module.get_module_config()
  repo = os.environ.get(ffconfig["repo_env"], ffconfig['repo'])
  repo_save_dir= os.path.join(build_cfg.get_samples_dir(), ffconfig['repo_save_dir'])
  ffmpeg_module.init_sample_repo(repo, repo_save_dir)
  
  # print(base.get_platform_envs(args))
  pass