# Product Store Manager

## Introduzione
Questo progetto è un servizio REST sperimentale scritto in Python, pensato per imparare a progettare e sviluppare un'applicazione ben strutturata con FastAPI, persistenza tramite SQLAlchemy/SQLite, gestione utenti e funzionalità CRUD per i prodotti. L'obiettivo principale è fornire una codebase modulare, testabile e facilmente estendibile.

### Indice 
- Requisiti
- Installazione
- Configurazione
- Esecuzione
- API
- Autenticazione
- Gestione Prodotti (CRUD)
- Test
- CI/CD e Quality
- Docker


Alberatura della cartella `app`

```
app/
├── __init__.py
├── config/
│   └── config.yml
├── logs/
│   └── app.log
└── src/
	├── __init__.py
	├── main.py
	├── __pycache__/
	│   ├── __init__.cpython-312.pyc
	│   └── main.cpython-312.pyc
	├── core/
	│   ├── __init__.py
	│   ├── config.py
	│   ├── logger.py
	│   ├── security.py
	│   └── db/
	├── exceptions/
	│   ├── __init__.py
	│   ├── base_exception.py
	│   ├── __pycache__/
	│   ├── product_exceptions/
	│   └── user_exceptions/
	├── models/
	├── routers/
	│   ├── __init__.py
	│   ├── deps.py
	│   ├── __pycache__/
	│   └── v1/
	├── schemas/
	│   ├── __init__.py
	│   ├── category_request.py
	│   ├── category_response.py
	│   ├── product_request.py
	│   ├── product_response.py
	│   ├── user_request.py
	│   ├── user_response.py
	│   └── __pycache__/
	└── services/
		├── __init__.py
		├── __pycache__/
		├── products/
		└── users/
```




