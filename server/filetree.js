"use strict";

const filetree = module.exports = new (require("events").EventEmitter)();

const _        = require("lodash");
const chokidar = require("chokidar");
const escRe    = require("escape-string-regexp");
const fs       = require("graceful-fs");
const path     = require("path");

const log      = require("./log.js");
const paths    = require("./paths.js").get();
const utils    = require("./utils.js");
const walker   = require("./walker.js");

let dirs     = {};
let todoDirs = [];
let initial  = true;
let watching = true;
let timer    = null;
let cfg      = null;

const WATCHER_DELAY = 3000;

filetree.init = function(config) {
  cfg = config;
  walker.init(cfg);
};

filetree.watch = function() {
  chokidar.watch(paths.files, {
    alwaysStat    : true,
    ignoreInitial : true,
    usePolling    : Boolean(cfg.pollingInterval),
    interval      : cfg.pollingInterval,
    binaryInterval: cfg.pollingInterval
  }).on("error", log.error).on("all", () => {
    // TODO: only update what's really necessary
    if (watching) filetree.updateAll();
  });
};

filetree.updateAll = _.debounce(() => {
  log.debug("Updating file tree because of local filesystem changes");
  filetree.updateDir(null, () => {
    filetree.emit("updateall");
  });
}, WATCHER_DELAY);

function lookAway() {
  watching = false;
  clearTimeout(timer);
  timer = setTimeout(() => {
    watching = true;
  }, WATCHER_DELAY);
}

function filterDirs(dirs) {
  return dirs.sort((a, b) => {
    return utils.countOccurences(a, "/") - utils.countOccurences(b, "/");
  }).filter((path, _, self) => {
    return self.every(another => {
      return another === path || path.indexOf(another + "/") !== 0;
    });
  }).filter((path, index, self) => {
    return self.indexOf(path) === index;
  });
}

const debouncedUpdate = _.debounce(() => {
  filterDirs(todoDirs).forEach(dir => {
    filetree.emit("update", dir);
  });
  todoDirs = [];
}, 100, {trailing: true});

function update(dir) {
  updateDirSizes();
  todoDirs.push(dir);
  debouncedUpdate();
}

function handleUpdateDirErrs(errs, cb) {
  errs.forEach(err => {
    if (err.code === "ENOENT" && dirs[utils.removeFilesPath(err.path)]) {
      delete dirs[utils.removeFilesPath(err.path)];
    } else {
      log.error(err);
    }
  });
  if (typeof cb === "function") cb();
}

filetree.updateDir = function(dir, cb) {
  if (dir === null) { dir = "/"; dirs = {}; }
  fs.stat(utils.addFilesPath(dir), (err, stat) => {
    if (err) log.error(err);
    if (initial) { // use sync walk for performance
      initial = false;
      const r = walker.walkSync(utils.addFilesPath(dir));
      if (r[0]) handleUpdateDirErrs(r[0]);
      updateDirInCache(dir, stat, r[1], r[2], cb);
    } else {
      log.debug("Updating cache of " + dir);
      walker.walk(utils.addFilesPath(dir), (errs, readDirs, readFiles) => {
        if (errs) handleUpdateDirErrs(errs, cb);
        updateDirInCache(dir, stat, readDirs, readFiles, cb);
      });
    }
  });
};

function updateDirInCache(root, stat, readDirs, readFiles, cb) {
  dirs[root] = {files: {}, size: 0, mtime: stat ? stat.mtime.getTime() : Date.now()};

  const readDirObj = {}, readDirKeys = [];
  readDirs.sort((a, b) => utils.naturalSort(a.path, b.path)).forEach(d => {
    const path = normalize(utils.removeFilesPath(d.path));
    readDirObj[path] = d.stat;
    readDirKeys[path] = path;
  });

  // Remove deleted dirs
  Object.keys(dirs).forEach(path => {
    if (path.indexOf(root) === 0 && readDirKeys.indexOf(path) === -1 && path !== root) {
      delete dirs[path];
    }
  });

  // Add dirs
  Object.keys(readDirObj).forEach(path => {
    dirs[path] = {
      files: {}, size: 0, mtime: readDirObj[path].mtime.getTime() || 0
    };
  });

  // Add files
  readFiles.sort((a, b) => {
    return utils.naturalSort(a.path, b.path);
  }).forEach(f => {
    const parentDir = normalize(utils.removeFilesPath(path.dirname(f.path)));
    dirs[parentDir].files[normalize(path.basename(f.path))] = {
      size: f.stat.size, mtime: f.stat.mtime.getTime() || 0
    };
    dirs[parentDir].size += f.stat.size;
  });

  update(root);
  if (typeof cb === "function") cb();
}

function updateDirSizes() {
  const todo = Object.keys(dirs);

  todo.sort((a, b) => {
    return utils.countOccurences(b, "/") - utils.countOccurences(a, "/");
  });

  todo.forEach(d => {
    dirs[d].size = 0;
    Object.keys(dirs[d].files).forEach(f => {
      dirs[d].size += dirs[d].files[f].size;
    });
  });

  todo.forEach(d => {
    if (path.dirname(d) !== "/" && dirs[path.dirname(d)]) {
      dirs[path.dirname(d)].size += dirs[d].size;
    }
  });
}

filetree.del = function(dir) {
  fs.stat(utils.addFilesPath(dir), (err, stats) => {
    if (err) log.error(err);
    if (!stats) return;
    if (stats.isFile()) {
      filetree.unlink(dir);
    } else if (stats.isDirectory()) {
      filetree.unlinkdir(dir);
    }
  });
};

filetree.unlink = function(dir) {
  lookAway();
  utils.rm(utils.addFilesPath(dir), err => {
    if (err) log.error(err);
    delete dirs[path.dirname('/')].files[path.basename(dir)];
    update(path.dirname('/'));
  });
};

filetree.unlinkdir = function(dir) {
  lookAway();
  utils.rm(utils.addFilesPath(dir), err => {
    if (err) log.error(err);
    delete dirs[dir];
    Object.keys(dirs).forEach(d => {
      if (new RegExp("^" + escRe(dir) + "/").test(d)) delete dirs[d];
    });
    update(path.dirname(dir));
  });
};

filetree.clipboard = function(src, dst, type) {
  fs.stat(utils.addFilesPath(src), (err, stats) => {
    lookAway();
    if (err) log.error(err);
    if (stats.isFile()) {
      filetree[type === "cut" ? "mv" : "cp"](src, dst);
    } else if (stats.isDirectory()) {
      filetree[type === "cut" ? "mvdir" : "cpdir"](src, dst);
    }
  });
};

filetree.mk = function(dir, cb) {
  lookAway();
  fs.stat(utils.addFilesPath(dir), err => {
    if (err && err.code === "ENOENT") {
      fs.open(utils.addFilesPath(dir), "wx", (err, fd) => {
        if (err) log.error(err);
        fs.close(fd, error => {
          if (error) log.error(error);
          dirs[path.dirname(dir)].files[path.basename(dir)] = {size: 0, mtime: Date.now()};
          update(path.dirname(dir));
          if (cb) cb();
        });
      });
    } else {
      if (cb) cb();
    }
  });
};

filetree.mkdir = function(dir, cb) {
  lookAway();
  fs.stat(utils.addFilesPath(dir), err => {
    if (err && err.code === "ENOENT") {
      utils.mkdir(utils.addFilesPath(dir), err => {
        if (err) log.error(err);
        dirs[dir] = {files: {}, size: 0, mtime: Date.now()};
        update(path.dirname(dir));
        if (cb) cb();
      });
    } else {
      if (cb) cb();
    }
  });
};

filetree.move = function(src, dst, cb) {
  lookAway();
  fs.stat(utils.addFilesPath(src), (err, stats) => {
    if (err) log.error(err);
    if (stats.isFile()) {
      filetree.mv(src, dst, cb);
    } else if (stats.isDirectory()) {
      filetree.mvdir(src, dst, cb);
    }
  });
};

filetree.moveTemps = function(src, dst, cb) {
  lookAway();
  utils.move(src, dst, cb);
};

filetree.mv = function(src, dst, cb) {
  lookAway();
  utils.move(utils.addFilesPath(src), utils.addFilesPath(dst), err => {
    if (err) log.error(err);
    dirs[path.dirname(dst)].files[path.basename(dst)] = dirs[path.dirname(src)].files[path.basename(src)];
    delete dirs[path.dirname(src)].files[path.basename(src)];
    update(path.dirname(src));
    update(path.dirname(dst));
    if (cb) cb();
  });
};

filetree.mvdir = function(src, dst, cb) {
  lookAway();
  utils.move(utils.addFilesPath(src), utils.addFilesPath(dst), err => {
    if (err) log.error(err);
    // Basedir
    dirs[dst] = dirs[src];
    delete dirs[src];
    // Subdirs
    Object.keys(dirs).forEach(dir => {
      if (new RegExp("^" + escRe(src) + "/").test(dir) && dir !== src && dir !== dst) {
        dirs[dir.replace(new RegExp("^" + escRe(src) + "/"), dst + "/")] = dirs[dir];
        delete dirs[dir];
      }
    });
    update(path.dirname(src));
    update(path.dirname(dst));
    if (cb) cb();
  });
};

filetree.cp = function(src, dst, cb) {
  lookAway();
  utils.copyFile(utils.addFilesPath(src), utils.addFilesPath(dst), () => {
    dirs[path.dirname(dst)].files[path.basename(dst)] = _.cloneDeep(dirs[path.dirname(src)].files[path.basename(src)]);
    dirs[path.dirname(dst)].files[path.basename(dst)].mtime = Date.now();
    update(path.dirname(dst));
    if (cb) cb();
  });
};

filetree.cpdir = function(src, dst, cb) {
  lookAway();
  utils.copyDir(utils.addFilesPath(src), utils.addFilesPath(dst), () => {
    // Basedir
    dirs[dst] = _.cloneDeep(dirs[src]);
    dirs[dst].mtime = Date.now();
    // Subdirs
    Object.keys(dirs).forEach(dir => {
      if (new RegExp("^" + escRe(src) + "/").test(dir) && dir !== src && dir !== dst) {
        dirs[dir.replace(new RegExp("^" + escRe(src) + "/"), dst + "/")] = _.cloneDeep(dirs[dir]);
        dirs[dir.replace(new RegExp("^" + escRe(src) + "/"), dst + "/")].mtime = Date.now();
      }
    });
    update(path.dirname(dst));
    if (cb) cb();
  });
};

filetree.save = function(dst, data, cb) {
  lookAway();
  fs.stat(utils.addFilesPath(dst), err => {
    if (err && err.code !== "ENOENT") return cb(err);
    fs.writeFile(utils.addFilesPath(dst), data, err => {
      dirs[path.dirname(dst)].files[path.basename(dst)] = {size: Buffer.byteLength(data), mtime: Date.now()};
      update(path.dirname(dst));
      if (cb) cb(err);
    });
  });
};

function entries(files, folders, relativePaths, base) {
  const entries = {};
  files.forEach(file => {
    const f = dirs[path.dirname(file)].files[path.basename(file)];
    const mtime = Math.round(f.mtime / 1e3);
    const name = relativePaths ? path.relative(base, file) : path.basename(file);
    entries[name] = ["f", mtime, f.size].join("|");
  });
  folders.forEach(folder => {
    if (dirs[folder]) {
      const d = dirs[folder];
      const mtime = Math.round(d.mtime / 1e3);
      const name = relativePaths ? path.relative(base, folder) : path.basename(folder);
      entries[name] = ["d", mtime, d.size].join("|");
    }
  });
  return entries;
}

filetree.search = function(query, p) {
  if (!dirs[p] || typeof query !== "string" || !query) return null;
  const files = [];
  const folders = [];
  query = query.toLowerCase();
  Object.keys(dirs).filter(dir => {
    return dir.indexOf(p) === 0;
  }).forEach(dir => {
    if (dir.toLowerCase().includes(query) && dir !== p) {
      folders.push(dir);
    }
    Object.keys(dirs[dir].files).forEach(file => {
      if (file.toLowerCase().includes(query)) {
        files.push(path.posix.join(dir, file));
      }
    });
  });
  const e = entries(files, folders, true, p);
  if (!Object.keys(e).length) return null;
  return e;
};

filetree.ls = function(p) {
  if (!dirs[p]) return;
  const files = Object.keys(dirs[p].files).map(file => {
    return path.posix.join(p, file);
  });
  const folders = [];
  Object.keys(dirs).forEach(dir => {
    if (path.dirname(dir) === p && path.basename(dir)) {
      folders.push(dir);
    }
  });
  return entries(files, folders);
};

filetree.lsFilter = function(p, re) {
  if (!dirs[p]) return;
  return Object.keys(dirs[p].files).filter(file => {
    return re.test(file);
  });
};

function normalize(str) {
  return String.prototype.normalize ? str.normalize() : str;
}
