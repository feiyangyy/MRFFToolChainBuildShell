from dataclasses import dataclass
import os
import sys
import git
from abc import ABC, abstractmethod

class BuildError(Exception):
  pass

class InstallError(Exception):
  pass

class InitError(Exception):
  pass

class ConfigureError(Exception):
  pass


class Repo(object):
  def __init__(self, repo_url, local_path, has_submodule=False):
    self.repo_url = repo_url
    self.path_to_clone = local_path
    self.__repo = None
    self.__has_sub = has_submodule
    if not os.path.exists(self.path_to_clone):
      print(f"Directory {self.path_to_clone} does not exist, make it.")
      os.makedirs(self.path_to_clone)
  
  def init(self):
    if os.path.exists(self.path_to_clone):
      self.__repo = git.Repo(self.path_to_clone)
    else:
      self.__repo = git.Repo.clone_from(self.repo_url, self.path_to_clone)
      print(f"{self.repo_url} is cloned into {self.path_to_clone}")
    if self.__has_sub:
      self.__repo.submodule_update(init=True, recursive=True)
      print("Submodules are updated")
  
  def get_repo_dir(self):
    return self.__repo.working_dir

  def create_local_branch_on_commit(self, branch_name, commit:str):
    self.__repo.commit(commit)
    branch = self.__repo.create_head(branch_name)
    branch.checkout()

  def apply_patches(self, patch_dir):
    old_dir = os.curdir()
    os.chdir(self.get_repo_dir())
    res = os.system(f"git am --whitespace=fix --keep {patch_dir}/*.patch")
    os.chdir(old_dir)
    if res:
      raise InitError(f"Apply patches failed for {self.get_repo_dir()} within {patch_dir}")
  
  def reset(self):
    if os.path.isdir(os.path.join(self.get_repo_dir(), '.git', 'rebase-apply')):
      self.__repo.git.am('--skip')

@dataclass
class BuildConfigure(object):
  platform: str
  arch: str
  workspace: str
  install_prefix: str
  action: str
  
  def prepare(self):
    if not os.path.exists(self.workspace):
      os.makedirs(self.workspace)
    if not os.path.exists(self.install_prefix):
      os.makedirs(self.install_prefix)
    if not os.path.exists(self.get_arch_workspace()):
      os.makedirs(self.get_arch_workspace())
    if not os.path.exists(self.get_patch_dir()):
      try:
        patch_dir = self.get_patch_dir()
        os.symlink(os.path.abspath('../../patches'), patch_dir)
      except FileExistsError:
        pass
      except:
        raise
    if not os.path.exists(self.get_samples_dir()):
      os.makedirs(self.get_samples_dir())
    
  def get_arch_workspace(self):
    return os.path.join(self.workspace, self.arch)
  
  def get_patch_dir(self):
    return os.path.join(self.workspace, "patches")
  
  def get_samples_dir(self):
    return os.path.join(self.workspace, "samples")
  

@dataclass
class HostVars(object):
  arch: str
  platform: str
  host_tag: str

def detect_host() -> HostVars:
  host=""
  if sys.platform == "darwin":
    host="darwin-x86_64"
  elif sys.platform == "linux":
    host="linux-x86_64"
  else:
    raise ConfigureError(f"Unknown host {sys.platform}")
  host_var = HostVars(arch="x86_64", platform=sys.platform, host_tag=host)
  return host_var
  


@dataclass
class ToolchainVars(object):
  triple_cc: str
  triple_cxx: str
  cc: str
  cxx: str
  as_tool: str
  yasm: str
  ar: str
  nm: str
  ranlib: str
  strip: str
  readelf: str
  size: str
  strings: str
  lipo: str
  sysroot: str
  make: str
  path:str
  
  def __post_init__(self):
    files= [
      self.triple_cc,
      self.triple_cxx,
      self.cc,
      self.cxx,
      self.as_tool,
      self.yasm,
      self.ar,
      self.nm,
      self.ranlib, 
      self.strip,
      self.readelf,
      self.size,
      self.strings,
      self.lipo,
      self.sysroot
    ]
    for f in files:
      if not os.path.exists(f):
        raise ConfigureError(f"Tool {f} does not exist")
  

def get_platform_env_android(cfg:BuildConfigure)-> tuple[ToolchainVars, HostVars]:
  env = {}
  ndk_home = env["ANDROID_NDK_HOME"] = os.environ["ANDROID_NDK_HOME"]
  if not os.path.exists(env["ANDROID_NDK_HOME"]):
    raise ConfigureError(f"ANDROID_NDK_HOME {env['ANDROID_NDK_HOME']} does not exist!")
  triple_cc=""
  ff_arch=""
  android_abi=""
  android_api_lv=21
  host_var = detect_host()
  if cfg.arch == "armv7a":
    triple=f"armv7a-linux-androideabi{android_api_lv}"
    ff_arch="armv7a"
    android_abi="armeabi-v7a"
  elif cfg.arch == "x86":
    triple=f"i686-linux-android{android_api_lv}"
    ff_arch="i686"
    android_abi="x86"
  elif cfg.arch == "x86_64":
    triple=f"x86_64-linux-android{android_api_lv}"
    ff_arch="x86_64"
    android_abi="x86_64"
  elif cfg.arch == "arm64":
    triple=f"aarch64-linux-android{android_api_lv}"
    ff_arch="aarch64"
    android_abi="arm64-v8a"

  else:
    raise ConfigureError(f"Unknown arch {cfg.arch} for platform {cfg.platform}")
  
  env["TRIPLE_CC"] = triple_cc
  env["FF_ARCH"] = ff_arch
  env["ANDROID_ABI"] = android_abi
  host_tag=host_var.host_tag
  env["TOOLCHAIN_ROOT"] = TOOLCHAIN_ROOT=f"{env['ANDROID_NDK_HOME']}/toolchains/llvm/prebuilt/{host_tag}"
  env["SYS_ROOT"]=f"{env['TOOLCHAIN_ROOT']}/sysroot"
  PATH_ENV=os.environ["PATH"]
  PATH_ENV=f"{env['TOOLCHAIN_ROOT']}/bin:{PATH_ENV}"
  env["PATH"] = PATH_ENV
  tvar = ToolchainVars(triple_cc=f"{TOOLCHAIN_ROOT}/bin/{triple}-clang",
                       triple_cxx=f"{TOOLCHAIN_ROOT}/bin/{triple}-clang++",
                       cc=f"{TOOLCHAIN_ROOT}/bin/clang",
                       cxx=f"{TOOLCHAIN_ROOT}/bin/clang++",
                       as_tool=f"{TOOLCHAIN_ROOT}/bin/llvm-as",
                       yasm=f"{TOOLCHAIN_ROOT}/bin/yasm",
                       ar=f"{TOOLCHAIN_ROOT}/bin/llvm-ar",
                       nm=f"{TOOLCHAIN_ROOT}/bin/llvm-nm",
                       ranlib=f"{TOOLCHAIN_ROOT}/bin/llvm-ranlib",
                       strip=f"{TOOLCHAIN_ROOT}/bin/llvm-strip",
                       readelf=f"{TOOLCHAIN_ROOT}/bin/llvm-readelf",
                       size=f"{TOOLCHAIN_ROOT}/bin/llvm-size",
                       strings=f"{TOOLCHAIN_ROOT}/bin/llvm-strings",
                       lipo=f"{TOOLCHAIN_ROOT}/bin/llvm-lipo",
                       sysroot=f"{env['SYS_ROOT']}",
                       make=f"{ndk_home}/prebuilt/{host_tag}/bin/make",
                       path=PATH_ENV)
  return (tvar, host_var)

def get_platform_envs(cfg:BuildConfigure):
  if cfg.platform == "android":
    return get_platform_env_android(cfg)
  else:
    raise ConfigureError(f"Unknown platform {cfg.platform}")


class FFModule(ABC):
  def __init__(self, cfg: BuildConfigure, toolchain:ToolchainVars, host:HostVars):
    """_summary_

    Args:
        cfg (BuildConfigure): 编译配置
    根据repo 要创建多个arch的base，因此要保留一个作为sample， 避免重复clone
    """
    self.cfg = cfg
    self.repo = None
    # will be initilaized by subclasses
    self.module_config = None
    
  @abstractmethod
  def get_module_config(self) ->dict:
    pass
  
  def init_sample_repo(self, repo_url, repo_save):
    # TODO fix the spelling
    self.repo = Repo(repo_url, repo_save, self.module_config.get("has_submodule", False))
    if not os.path.exists(repo_save):
      self.repo.clone()
      return
    
    # check if there is a patch
    print(f"Sample repo {repo_save} exists, skip cloing!")

  
  def copy_sample_to(self, target_dir):
    if not self.repo:
      raise InitError("No repo, maybe not initialized?")
    par = os.path.dirname(target_dir)
    if not os.path.exists(par):
      os.makedirs(par)
    print(f"Copy {self.repo.path_to_clone} to {target_dir}")
    ret = os.system(f"cp -rf {self.repo.path_to_clone} {target_dir}")
    if ret != 0:
      raise BuildError(f"Copy {self.repo.path_to_clone} to {target_dir} failed")
  
  def copy_sample_to_arch(self, parent_dir:str):
    target = f"{parent_dir}/{self.cfg.arch}"
    self.copy_sample_to(target)
  
  @abstractmethod
  def do_init():
    """do the initialization
    1. clone the source code, or download the library
    2. prepare all the patches
    """
    pass

  @abstractmethod
  def do_install_prebuilt():
    """install the prebuilt libraries
    if no prebuilt, an error will be raised.
    """
    pass
  
  @abstractmethod
  def prebuild(self):
    """jobs before building
    1. copy to arch
    2. apply patches
    3. detect and setup third libraries
    4. prepare the directories
    """
    pass
  
  @abstractmethod
  def build(self, toolchain_vars: dict, host_vars: dict):
    """do the build work

    Args:
        toolchain_vars (dict): the detected toolchain variables
        host_vars: the detected host variables
    """
    pass
  
  @abstractmethod
  def postbuild(self):
    """dirty works after build
    """
    pass
  