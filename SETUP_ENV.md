# Configuración del Entorno - Evolución Industria Videojuegos

## Paso 1: Crear y activar el entorno virtual

### Windows (PowerShell)
```powershell
cd "c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof"
python -m venv mmc_python_lab
.\mmc_python_lab\Scripts\Activate.ps1
```

### Windows (CMD)
```cmd
cd "c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof"
python -m venv mmc_python_lab
mmc_python_lab\Scripts\activate.bat
```

### Mac / Linux
```bash
cd "/ruta/a/proof"
python3 -m venv mmc_python_lab
source mmc_python_lab/bin/activate
```

## Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 3: Configurar credenciales (.env)

1. Copia `.env.example` a `.env`
2. Rellena las variables según la tabla inferior

| Variable | Obligatorio | Dónde obtenerla |
|----------|-------------|-----------------|
| `KAGGLE_USERNAME` | **Sí** | Kaggle.com → Account → API → Create New Token |
| `KAGGLE_KEY` | **Sí** | Mismo archivo kaggle.json que descargas |
| `RAWG_API_KEY` | Opcional | [rawg.io/developer](https://rawg.io/login/?forward=developer) |

**Nota Kaggle:** Coloca el archivo `kaggle.json` en:
- **Windows:** `C:\Users\<tu_usuario>\.kaggle\kaggle.json`
- **Mac/Linux:** `~/.kaggle/kaggle.json`

O bien define `KAGGLE_USERNAME` y `KAGGLE_KEY` en tu `.env`.

## Paso 4: Ejecutar el notebook

```bash
jupyter notebook 01_data_extraction.ipynb
```
