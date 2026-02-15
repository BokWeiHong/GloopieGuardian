const fs = require('fs');
const path = require('path');

const pcapFile = process.argv[2];
if (pcapFile && fs.existsSync(pcapFile)) {
  const dest = path.join(__dirname, 'src', 'assets', 'auto.pcap');
  fs.copyFileSync(pcapFile, dest);
  console.log(`Copied ${pcapFile} to ${dest}`);
} else if (pcapFile) {
  console.error(`File ${pcapFile} does not exist`);
}

const { spawn } = require('child_process');
const ngServe = spawn('ng', ['serve', '--proxy-config', 'src/proxy.conf.json', '--host=0.0.0.0', '--port=8085', '--disable-host-check'], {
  stdio: 'inherit',
  cwd: __dirname
});

ngServe.on('close', (code) => {
  process.exit(code);
});