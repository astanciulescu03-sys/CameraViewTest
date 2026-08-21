# CameraX

Aplicatie desktop (Python + PySide6) pentru monitorizarea camerelor IP din reteaua locala:
scanare retea, adaugare camere (ONVIF automat sau RTSP manual), vizualizare live si
inregistrare video in folderul ales de tine.

## Instalare

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Rulare

```
python main.py
```

## Utilizare

La prima pornire, fereastra principala e goala si te invita sa adaugi o camera din
**⚙ Setari** (buton in coltul din dreapta-sus). De la a doua pornire incolo, aplicatia
deschide automat, direct pe ecran, feed-ul live al camerei principale salvate - nu mai
trebuie sa selectezi nimic.

### ⚙ Setari

- **Camere** - scaneaza reteaua (ONVIF + port RTSP 554) sau adauga manual o camera
  (RTSP direct sau detectare automata ONVIF). La adaugare (sau prin **"Editeaza
  camera"** ulterior) alegi folderul de salvare si **perioada maxima de pastrare**
  (ore sau zile) - specifica fiecarei camere. Butonul **"Foloseste ca principala"**
  stabileste care camera se deschide automat la pornirea aplicatiei. Prima camera
  adaugata devine automat principala.
- **Overlay data/ora** - suprapune peste imagine (atat in preview, cat si in fisierul
  salvat) data si ora curenta, luate din sistem - separat de orice overlay propriu al
  camerei. Poate fi dezactivat sau mutat in oricare colt al imaginii.

### Inregistrare continua, ca la o camera auto

De indata ce o camera devine principala (are folder + perioada de pastrare setate),
**inregistrarea porneste automat** - nu trebuie apasat niciun buton:

- Filmarile se taie in fisiere `.mp4` de **maxim 1 ora**; cand se termina unul, urmatorul
  porneste imediat, fix unul dupa altul, fara pauza.
- Cand se depaseste perioada de pastrare setata pentru camera respectiva (ex: 3 zile),
  cele mai vechi fisiere se sterg automat, pe masura ce apar altele noi - exact ca la
  bucla de inregistrare a unei camere auto (dashcam). Verificarea se face la fiecare
  segment nou si, ca plasa de siguranta, din ora in ora pentru toate camerele.
- Din ecranul principal poti oricand **opri/reporni manual** inregistrarea cu butonul
  dedicat (util daca vrei sa pui pauza temporar), fara sa afecteze setarile camerei.
- Daca legatura cu camera se pierde, aplicatia incearca automat sa se reconecteze la
  fiecare 5 secunde, fara interventie.

Toate setarile (camere, camera principala, folder, perioada de pastrare, overlay) se
salveaza automat in `%USERPROFILE%\.camerax\config.json`.

## Ruleaza in system tray

Inchiderea ferestrei (X) nu opreste aplicatia - o minimizeaza in system tray (langa
ceas), iar feed-ul/inregistrarea continua in fundal. Din iconita din tray (camera pe
fundal bleumarin):

- **click / dublu-click** - redeschide fereastra
- **click dreapta -> Setari** - deschide direct setarile
- **click dreapta -> Iesire** - inchide aplicatia complet (opreste feed-ul si iese)

## Build executabil (.exe, fara consola)

```
.venv\Scripts\activate
pip install -r requirements-dev.txt
pyinstaller --noconfirm --clean CameraX.spec
```

Rezultatul e `dist\CameraX.exe` - un singur fisier, fara fereastra de consola, cu
iconita proprie (`assets\icon.ico`, generata cu `scripts\make_icon.py`). Poti sa-l
copiezi oriunde si sa-l pui la pornirea Windows (Task Scheduler sau shortcut in
`shell:startup`) ca sa porneasca automat cu camera principala.

## Note

- Descoperirea ONVIF (WS-Discovery) necesita pachetul `WSDiscovery`; daca nu se
  instaleaza pe sistemul tau, scanarea de retea foloseste in continuare fallback-ul
  pe port RTSP (554), iar adaugarea manuala functioneaza mereu.
- Multe camere ONVIF necesita autentificare (utilizator + parola) chiar si pentru
  descoperirea stream-ului - completeaza-le in tab-ul ONVIF inainte de a apasa
  "Detecteaza stream".
- Aplicatia afiseaza si inregistreaza o singura camera (cea principala) o data - daca
  vrei sa monitorizezi alta camera, seteaz-o ca principala din Setari.
