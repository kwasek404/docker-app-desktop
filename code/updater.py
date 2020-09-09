#!/usr/bin/env python

import logging
import requests
import sys
import os
import yaml
import re
import datetime

class main():
  mainDir = None
  images = None

  def __init__(self):
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s', stream=sys.stdout)
    self.mainDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    with open('{}/../images.yaml'.format(self.mainDir), 'r') as f:
      self.images = yaml.load(f, Loader=yaml.SafeLoader)

  def getDockerfile(self, dir, dockerfile):
    logging.info('Reading file: {}/{}'.format(dir, dockerfile))
    with open('{}/../{}/{}'.format(self.mainDir, dir, dockerfile), 'r') as f:
      return f.read()
  
  def updateDockerfile(self, dir, dockerfile, content):
    logging.info('Writing file: {}/{}'.format(dir, dockerfile))
    with open('{}/../{}/{}'.format(self.mainDir, dir, dockerfile), 'w') as f:
      return f.write(content)
  
  def getFromVariables(self, content):
    return re.findall(r'^FROM .*', content)
  
  def getFromDecode(self, fromValue):
    return fromValue.split()[1].split(':')
  
  def checkAndUpdateVersionsRegistry(self, content, dir, dockerfile):
    change = False
    froms = self.getFromVariables(content)
    for fromValue in froms:
      fromImage, fromVersion = self.getFromDecode(fromValue)
      logging.info('File image: {}, tag: {}'.format(fromImage, fromVersion))
      latestVersion = self.getRegistryLatest(fromImage)
      if fromVersion != latestVersion:
        logging.info('Image: {}, update {} -> {}'.format(fromImage, fromVersion, latestVersion))
        content = content.replace(fromValue, 'FROM {}:{}'.format(fromImage, latestVersion))
        change = True
    if change:
      self.updateDockerfile(dir, dockerfile, content)
    return change

  def getRegistryLatest(self, fromImage):
    if fromImage.find('/') == -1:
      owner = 'library'
      image = fromImage
    else:
      owner, image = fromImage.split('/')
    URL = "https://registry.hub.docker.com/v2/repositories/{}/{}/tags".format(owner, image)
    response = requests.get(URL).text
    responseYaml = yaml.load(response, Loader=yaml.SafeLoader)
    newestTag = None
    newestVersion = None
    for upload in responseYaml['results']:
      if upload['name'] != 'latest':
        if newestVersion == None:
          newestTag = upload['name']
          newestVersion = datetime.datetime.strptime(upload['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
          tmp = datetime.datetime.strptime(upload['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ')
          if tmp > newestVersion:
            newestTag = upload['name']
            newestVersion = tmp
    logging.info("Registry latest image: {}, tag: {}, upload: {}".format(image, newestTag, newestVersion))
    return newestTag


  def main(self):
    logging.info(self.images)
    for template in self.images['templates']:
      content = self.getDockerfile(template['dir'], template['dockerfile'])
      updateStatus = self.checkAndUpdateVersionsRegistry(content, template['dir'], template['dockerfile'])
      for image in template['images']:
        print(image)

if __name__ == '__main__':
  main().main()
