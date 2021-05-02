#testni API klic za PTZ kamere

  try:
      response = requests.get('https://9to5mac.com/', timeout=5)
      response.raise_for_status()
  except requests.exceptions.HTTPError as errh:
      print(errh)
  except requests.exceptions.ConnectionError as errc:
      print(errc)
  except requests.exceptions.Timeout as errt:
      print(errt)
  except requests.exceptions.RequestException as err:
      print(err)
