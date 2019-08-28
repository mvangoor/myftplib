class myftplib:
  _host = None
  _port = None
  _user = None
  _pass = None
  _connection = None
  _pret = False

  def __init__(self, host, port, user, passw):
    self._host = host
    self._port = port
    self._user = user
    self._pass = passw
    self.connect()

  def enable_pret(self):
    """Enable pre transfer support
    http://www.drftpd.org/index.php/PRET_Specifications"""
    print('Enabling PRET Support')
    self._pret = True

  def disable_pret(self):
    """Disable pre transfer support.
    http://www.drftpd.org/index.php/PRET_Specifications"""
    print('Disabling PRET Support')
    self._pret = False
	
  def connect(self):
    #print('Connecting...')
    self._connection = ftplib.FTP_TLS()
    #self._connection.set_debuglevel(2)
    self._connection.ssl_version = ssl.PROTOCOL_TLS
    self._connection.connect(self._host, self._port)
    self._connection.login(self._user, self._pass)
    self._connection.prot_p()
    self._connection.set_pasv(True)
    features = self._connection.voidcmd('FEAT')
    if re.search('PRET', features, re.M):
      self.enable_pret()

  def cwd(self, location):
    if not self._connection:
      self.connect()

    if self._connection:
      if '//' in location:
        location = location.replace('//', '/')

      return self._connection.cwd(location)

    return None

  def getListing(self):
    if not self._connection:
      self.connect()

    if self._connection:
      files = []
      parsed = []

      files = self._connection.voidcmd('STAT -L')

      for entry in files.split('\n'):
        #print('PRE: ['+entry+']')
        if entry.startswith('total'):
          continue

        parsed.append(parse_list(entry))

      return parsed

    return None

  def isDirectory(self, entry):
    if entry:
      if entry['directory']:
        if entry['directory'] == 'd':
          return True

    return False

  def download(self, src, dst, recursive=True):
    release = os.path.basename(os.path.normpath(src))
    dst = dst+'/'+release
    print('Download ['+src+'] to ['+dst+'], recursive: ['+str(recursive)+']')
    if not os.path.isdir(dst):
      os.mkdir(dst)
    
    org_pwd = os.getcwd()
    os.chdir(dst)
    self._download(src, dst, recursive)
    # Start the download
    os.chdir(org_pwd)

  def _download(self, src, dst, recursive):
    self.cwd(src)
    filelist = ftp.getListing()
    # print(filelist)
    if filelist:
      for entry in filelist:
        if entry:
          if ftp.isDirectory(entry):
            if recursive:
              #if entry['name'] == '.' or entry['name'] == '..':
              #  continue
              found = False
              for skip in skip_dirs:
                #print('match: ['+skip+'] <-> ['+entry['name']+']')
                if re.match(skip, entry['name'], re.I) or re.search(skip, entry['name'], re.I):
                  found = True
                  
              if not found:
                new_dst = dst + '/' + entry['name']
                print('Create directory -> ['+new_dst+']')
                #os.mkdir('./'+entry['name'])
                #self._download(entry, dst, recursive)
  
          else:
            # print(entry)
            try:
              if self._pret:
                self._connection.voidcmd('PRET RETR '+entry['name'])
              with open(entry['name'], 'wb') as f:
                self._connection.retrbinary('RETR '+entry['name'], f.write)
              print('Downloaded ['+entry['name']+']')
            except FileNotFoundError:
              print('Download failed for ['+entry['name']+']')
  
