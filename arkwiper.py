import os
import psutil

packages_path = f"{os.environ['LOCALAPPDATA']}/packages"
wipe_cluster_data = True


def kill() -> bool:
    for p in psutil.process_iter():
        if p.name() == "ShooterGame.exe":
            p.kill()
            return True
    else:
        return False


def wipe():
    for packagename in os.listdir(packages_path):
        if "StudioWildcard" not in packagename:
            continue
        local = f"{packages_path}/{packagename}/LocalState"
        if not os.listdir(local):
            continue
        saved = f"{local}/Saved"
        if wipe_cluster_data:
            cpath = f"{saved}/clusters/solecluster/"
            for cname in os.listdir(cpath):
                if "sync" in cname:
                    continue
                os.remove(os.path.join(cpath, cname))

        maps = f"{saved}/Maps"
        for foldername in os.listdir(maps):
            if "ClientPaintingsCache" in foldername:
                continue
            if "sync" in foldername:
                continue
            mapfolder = f"{maps}/{foldername}"

            # Only the island has no subfolder
            subfolder = True
            if foldername == "SavedArks":
                subfolder = False

            if not subfolder:
                mapcontents = os.listdir(mapfolder)
            else:
                mapfolder = f"{mapfolder}/{os.listdir(mapfolder)[0]}"
                mapcontents = os.listdir(mapfolder)

            for item in mapcontents:
                if "ServerPaintingsCache" in item:
                    continue
                if "BanList" in item:
                    continue
                if os.path.isdir(os.path.join(mapfolder, item)):
                    continue
                os.remove(os.path.join(mapfolder, item))


wipe()
