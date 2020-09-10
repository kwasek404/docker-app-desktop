#!/usr/bin/env python

import logging
import requests
import sys
import os
import yaml
import re
import datetime
import difflib

class main():
  mainDir = None
  images = None

  def __init__(self):
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s', stream=sys.stdout)
    self.mainDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    with open('{}/../images.yaml'.format(self.mainDir), 'r') as f:
      self.images = yaml.load(f, Loader=yaml.SafeLoader)

  def getFile(self, dir, filename):
    logging.info('Reading file: {}/{}'.format(dir, filename))
    try:
      with open('{}/../{}/{}'.format(self.mainDir, dir, filename), 'r') as f:
        return f.read()
    except FileNotFoundError:
      logging.info('Missing file: {}/{}'.format(dir, filename))
      return ''
  
  def overwriteFile(self, dir, filename, content):
    logging.info('Writing file: {}/{}'.format(dir, filename))
    self.checkAndCreateDir(dir)
    with open('{}/../{}/{}'.format(self.mainDir, dir, filename), 'w') as f:
      return f.write(content)
  
  def getFromVariables(self, content):
    return re.findall(r'^FROM .*', content)
  
  def getFromDecode(self, fromValue):
    return fromValue.split()[1].split(':')
  
  def checkAndCreateDir(self, dir):
    if not os.path.exists(dir):
      logging.info('Dir: {} doesnt exists, creating'.format(dir))
      os.makedirs(dir)
  
  def getMultilineDiff(self, a, b):
    return ''.join(difflib.ndiff(a.splitlines(1), b.splitlines(1)))
  
  def checkAndUpdateVersionsRegistry(self, dir, dockerfile, yamlcontent):
    currentContent = self.getFile(dir, dockerfile)
    fromValue = self.getFromVariables(yamlcontent)[0]
    fromImage, fromVersion = self.getFromDecode(fromValue)
    latestVersion = self.getRegistryLatest(fromImage)
    yamlcontent = yamlcontent.replace(fromValue, 'FROM {}:{}'.format(fromImage, latestVersion))
    if yamlcontent != currentContent:
      logging.info('Updating image')
      logging.info("DIFF:\n{}".format(self.getMultilineDiff(currentContent, yamlcontent)))
      self.overwriteFile(dir, dockerfile, yamlcontent)
      return self.checkAndUpdateVersionFile(dir, latestVersion)
    return self.getFile(dir, 'version')
  
  def checkAndUpdateVersionFile(self, dir, version):
    versionFile = 'version'
    content = self.getFile(dir, versionFile)
    if content == '' or version != ''.join(content.split('.')[:-1]):
      versionWithBuild = '{}.01'.format(version)
    else:
      versionWithBuild = '{}.{:02d}'.format(version, int(content.split('.')[-1])+1)
    if content != versionWithBuild:
      logging.info('Updating version')
      logging.info("DIFF:\n{}".format(self.getMultilineDiff(content, versionWithBuild)))
      self.overwriteFile(dir, versionFile, versionWithBuild)
    return versionWithBuild


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

  def checkAndUpdateAurImage(self, dir, dockerfile, entrypointfile, dockerfilecontent, entrypointcontent, templateVersion):
    change = False
    currentContent = self.getFile(dir, dockerfile)
    currentEntrypoint = self.getFile(dir, entrypointfile)
    fromValue = self.getFromVariables(dockerfilecontent)[0]
    fromImage, fromVersion = self.getFromDecode(fromValue)
    dockerfilecontent = dockerfilecontent.replace(fromValue, 'FROM {}:{}'.format(fromImage, templateVersion))
    if dockerfilecontent != currentContent:
      logging.info('Updating image')
      logging.info("DIFF:\n{}".format(self.getMultilineDiff(currentContent, dockerfilecontent)))
      self.overwriteFile(dir, dockerfile, dockerfilecontent)
      change = True
    if entrypointcontent != currentEntrypoint:
      logging.info('Updating entrypoint')
      logging.info("DIFF:\n{}".format(self.getMultilineDiff(currentEntrypoint, entrypointcontent)))
      self.overwriteFile(dir, entrypointfile, entrypointcontent)
      change = True
    if change:
      self.checkAndUpdateVersionFile(dir, latestVersion)


  def main(self):
    logging.info(self.images)
    for template in self.images['templates']:
      templateVersion = self.checkAndUpdateVersionsRegistry(template['dir'], 'Dockerfile', template['dockerfilecontent'])
      for image in template['images']:
        self.checkAndUpdateAurImage(image['dir'], 'Dockerfile', 'entrypoint.sh', image['dockerfilecontent'], image['entrypointcontent'], templateVersion)
        print(image)

if __name__ == '__main__':
  main().main()
