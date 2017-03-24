def get():
    with open("size_setting.txt","r") as fichier:
        return int(fichier.read())*1,91+1