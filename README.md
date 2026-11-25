# Flock Logbook: Poultry Heat-Stress Advisor

This is a small web app that tells a broiler farmer in Solwezi, Zambia how risky the next 72 hours of weather are for her flock, hour by hour, and what to do about it.

- **Deployed app (through the load balancer):** http://16.60.157.51/
- **Demo video (2 minutes max):** [ADD YOUR VIDEO LINK HERE]
- **Repository:** https://github.com/swendo-ace/poultry-advisor

The app is served over plain HTTP, so browsers show "Not secure". HTTPS would need a domain name and a certificate, which this assignment does not provide.

## The problem

Broilers cope badly with heat, and heat combined with humidity is worse than either alone. A farmer with a few hundred birds usually decides by feel: look at the sky, feel the air, hope. This app turns the hourly forecast into a risk level for the birds' actual size, so the farmer knows which hours need extra ventilation and cool water before the birds are already struggling.

The flock this was designed around is a small broiler flock near Solwezi, Zambia, so the forecast location is fixed to Solwezi (latitude -12.1688, longitude 26.3894).

## Features

- Enter the **hatch or arrival date** of the birds, or type a **measured average weight** in kg. If you type a weight, it is used instead of the date.
- Hourly forecast for the next 72 hours with temperature, humidity and a risk tier: Normal, Watch, High or Critical.
- A summary line showing the worst risk in the next 24 hours and a plain action for it (for example "Increase airflow, give cool water, keep birds calm").
- **Sort** the table by clicking any column heading.
- **Filter** by risk tier with the dropdown.
- Clear error messages for a bad date, a bad weight, or the weather service being unreachable.
- Every response carries an `X-Served-By` header with the server's hostname, which is how load balancing is verified.

## How it works

```
Browser --> Internet --> lb-01 (Nginx) --> web-01 (Nginx + gunicorn + Flask) --> Open-Meteo API
                                       \-> web-02 (Nginx + gunicorn + Flask) --> Open-Meteo API
```

| File | Purpose |
|---|---|
| `app.py` | Flask app: serves the page and the `/api/forecast` endpoint |
| `weather.py` | Calls Open-Meteo and pairs temperature and humidity for each hour |
| `risk.py` | Heat-stress calculation: wet-bulb temperature, THI, weight lookup, risk tiers |
| `static/index.html` | The page: input form, summary, sortable and filterable table |
| `requirements.txt` | Python dependencies |
| `test_api.py` | The first test call I made to Open-Meteo before building anything else |

### The risk calculation

1. Temperature and relative humidity for each hour are turned into a wet-bulb temperature (Stull 2011 approximation).
2. A broiler temperature-humidity index (THI) is computed as 0.85 x dry-bulb + 0.15 x wet-bulb.
3. Heavier birds start to overheat at a lower THI, so the app looks up the THI where stress begins for the bird's weight, interpolating between a few published reference points. Birds lighter than the lowest reference point use that point's value, which makes the app slightly over-cautious for young birds.
4. The gap between the hour's THI and that onset THI decides the tier: more than 2 below onset is Normal, 0 to 2 below is Watch, 0 to 2 above is High, more than 2 above is Critical.
5. If only a hatch date is given, weight is estimated from age using a table of typical broiler weights.

## API used

**Open-Meteo Forecast API**, free weather data.

- Documentation: https://open-meteo.com/en/docs
- Endpoint used: `https://api.open-meteo.com/v1/forecast`
- Parameters used: `latitude`, `longitude`, `hourly=temperature_2m,relative_humidity_2m`, `timezone=Africa/Lusaka`, `forecast_days=3`
- **No API key is needed.** The calls work without one, so there are no keys or secrets anywhere in this repository.

## Run it locally

You need Python 3.8 or newer.

Windows (PowerShell):

```powershell
git clone https://github.com/swendo-ace/poultry-advisor.git
cd poultry-advisor
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Mac or Linux:

```bash
git clone https://github.com/swendo-ace/poultry-advisor.git
cd poultry-advisor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000/ and enter a hatch date from the last 70 days (or a weight in kg) and click **Check risk**.

If PowerShell refuses to run the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

### The JSON endpoint

```
GET /api/forecast?hatch_date=YYYY-MM-DD
GET /api/forecast?weight=1.2
```

It returns `server`, `age_days`, `weight_kg` and a list of 72 `readings`, each with `time`, `temp_c`, `humidity`, `gap`, `tier` and `action`. Errors come back as JSON with an `error` message: status 400 for bad input, 502 if the weather service cannot be reached.

## Deployment

| Server | Role | IP |
|---|---|---|
| 7427-web-01 | App server | 13.43.215.90 |
| 7427-web-02 | App server | 18.171.151.6 |
| 7427-lb-01 | Load balancer | 16.60.157.51 |

All three run Ubuntu 20.04 with Python 3.8.10. I logged in with `ssh -i ~/.ssh/school ubuntu@<ip>`.

### On web-01 and web-02 (identical steps)

1. Install the tools and fetch the code:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git nginx
cd ~
git clone https://github.com/swendo-ace/poultry-advisor.git
cd poultry-advisor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the app with gunicorn as a systemd service, so it starts on boot and restarts if it crashes. `/etc/systemd/system/poultry.service`:

```ini
[Unit]
Description=Poultry advisor
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/poultry-advisor
ExecStart=/home/ubuntu/poultry-advisor/venv/bin/gunicorn -b 127.0.0.1:5000 -w 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now poultry
```

3. Put Nginx in front on port 80. `/etc/nginx/sites-available/default`:

```nginx
server {
    listen 80 default_server;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t && sudo systemctl restart nginx
```

4. Check it on the server: `curl -s "localhost/api/forecast?hatch_date=2026-10-25" | head -c 300`

### On lb-01

```bash
sudo apt update
sudo apt install -y nginx
```

`/etc/nginx/sites-available/default`:

```nginx
upstream poultry {
    server 13.43.215.90;
    server 18.171.151.6;
}

server {
    listen 80 default_server;
    location / {
        proxy_pass http://poultry;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t && sudo systemctl restart nginx
```

Nginx's default behaviour for an `upstream` group is round-robin, so requests alternate between the two web servers.

### Updating after a code change

```bash
cd ~/poultry-advisor && git pull
sudo systemctl restart poultry
```

Run this on both web servers.

## Testing the load balancer

From my laptop I sent six requests to the load balancer and printed which server answered each one:

```powershell
1..6 | ForEach-Object { (Invoke-WebRequest "http://16.60.157.51/api/forecast?hatch_date=2026-10-25" -UseBasicParsing).Headers["X-Served-By"] }
```

The result alternated `7427-web-01`, `7427-web-02`, `7427-web-01`, `7427-web-02`, `7427-web-01`, `7427-web-02`. I also opened http://16.60.157.51/ in a browser and checked that the form, summary, table, sorting and filtering all work. [ADD A SCREENSHOT OF THE ALTERNATING OUTPUT TO THE REPO AND LINK IT HERE]

## Error handling

- Bad or missing date or weight: the API returns a 400 with a readable message, and the page shows it in red.
- A hatch date in the future or more than 70 days old is rejected with an explanation.
- Weather service down or returning something unexpected: the API returns a 502 and the page says it cannot reach the weather data, instead of crashing.
- Hours with missing readings are skipped.

## Security and credentials

- There are no API keys and no login, so there are no credentials to share. Open-Meteo is used without a key.
- `.gitignore` excludes `venv/`, `.env` and `__pycache__/`, so nothing local or secret is committed.
- My SSH private key stays on my laptop and is never committed.

## Design decisions and limitations

- **Weight beats age.** The heat-stress research I used is organised by body weight, not age, so the app converts age to weight when it has to. Typing a real weight is more accurate.
- **The tier cutoffs are my own choice.** The 2-unit bands around the onset point are not a published standard. I picked them as a simple, explainable way to turn the gap into four levels. [ADD YOUR OWN REASONING FOR THIS CHOICE, AND WHAT YOU WOULD CHECK WITH A POULTRY EXPERT]
- **Some inputs are not independently verified.** The THI formula and the onset values come from a secondary summary of published research, and I have not checked them against the original papers. The age-to-weight table comes from figures a local broiler farmer gave me, not from a breeder's performance guide. Treat the output as guidance, not a measurement.
- **The reference weights start at 1.5 kg**, so young birds under that use the lowest reference value, which errs on the side of caution.
- **Altitude.** Solwezi is about 1,381 m above sea level, and the wet-bulb formula assumes sea-level pressure, so the numbers are slightly approximate.
- **One location.** The forecast is fixed to Solwezi.
- **HTTP only**, as noted at the top.

## Challenges and how I solved them

- **SSH "Permission denied (publickey)".** My first login attempts used the key I had made for GitHub. The servers were configured with the separate `school` key I registered on my intranet profile, and switching to that key fixed it.
- **Commands ran on the wrong machine.** After the failed login I kept pasting server commands, which ran on my own laptop and created a stray nested copy of the project. I deleted the extra folder and learned to check that the prompt shows `ubuntu@...` before pasting.
- **502 Bad Gateway on web-01.** Nginx was fine but gunicorn was not running, because the long block of commands I pasted had not fully executed (the project folder did not exist yet). Running the install steps in smaller groups, then restarting the service, fixed it.
- **Empty table on the deployed page.** The summary showed but the table did not. Viewing the page source showed the drawing code referred to a variable that did not exist. One corrected word and a `git pull` on both servers fixed it.
- [ADD ONE OR TWO CHALLENGES IN YOUR OWN WORDS, AND WHAT YOU WOULD DO DIFFERENTLY]

## Credits

- Weather data: [Open-Meteo](https://open-meteo.com), terms at https://open-meteo.com/en/terms
- [Flask](https://flask.palletsprojects.com), [Requests](https://requests.readthedocs.io), [Gunicorn](https://gunicorn.org) and [Nginx](https://nginx.org)
- Heat stress background: Butcher, G. D. and Miles, R., *Heat Stress Management in Broilers*, UF/IFAS Extension (EDIS VM019), https://edis.ifas.ufl.edu/publication/VM019
- Wet-bulb approximation: Stull, R. (2011), "Wet-Bulb Temperature from Relative Humidity and Air Temperature", Journal of Applied Meteorology and Climatology
- Broiler temperature-humidity index as reported from Tao and Xin (2003), cited through a secondary summary and not read in the original
- Typical broiler weights by age: figures from a local broiler farmer in Zambia
- Course material and the professor's architecture diagram for the two-server and load balancer layout

I wrote this README with the assistance of AI, as the course brief allows for the README.
