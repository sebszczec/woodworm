import requests

class Ip:
    def __init__(self):
        pass
    
    @staticmethod
    def get_external_ip_requests():
        try:
            response = requests.get('https://api.ipify.org')
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"Error HTTP: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"Error during query: {e}"