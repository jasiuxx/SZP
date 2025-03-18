from django.template import RequestContext

def global_context_processor(request):
    role_names = {
        'PO': 'Praktyczny Organizator',
        'NL': 'Naturalny Lider',
        'CZA': 'Człowiek Akcji',
        'SIE': 'Siewca (Człowiek Idei)',
        'CZK': 'Człowiek Kontaktów',
        'SE': 'Sędzia',
        'CZG': 'Człowiek Grupy',
        'PER': 'Perfekcjonista'
    }
    return {'role_names': role_names}
