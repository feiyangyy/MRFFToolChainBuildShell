import os
import sys
import git

class Repo(object):
  def __init__(self, repo_url, local_path):
    self.repo_url = repo_url
    self.path_to_clone = local_path
    if not os.path.exists(self.path_to_clone):
      print(f"Directory {self.path_to_clone} does not exist, make it.")
      os.makedirs(self.path_to_clone)
  
  def clone(self):
    git.Repo.clone_from(self.repo_url, self.path_to_clone)
    print(f"{self.repo_url} is cloned into {self.path_to_clone}")
  
  