import json
import ssl
import requests

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context
search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc" \
             "&term=Kyle+Kroll&retmode=json&retmax=500" \
             "&tool=reevestool&email=kylekroll@outlook.com"
pmc_ids = requests.get(search_url)
pmc_ids = pmc_ids.json()

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&retmode=json&tool=my_tool&email=my_email@example.com&id="
pmc_ids = pmc_ids['esearchresult']['idlist']
n = 200
chunks = [pmc_ids[i:i + n] for i in range(0, len(pmc_ids), n)]
for chunk in chunks:
    detailed_url = url + ",".join(chunk)
    print(detailed_url)
    details = requests.post(detailed_url).json()
    #print(json.dumps(details, indent=4))



