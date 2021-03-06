from django.shortcuts import render
from django.db.models import Sum, Q, Count
from . import utils
from . import models as m


def fetch_battles():
    for b in m.Battle.objects.all():
        p = ', '.join(utils.get_participants(b))
        t_dam = b.events.aggregate(Sum('damage'))['damage__sum']
        d = {
            # Stores data from usual Battle entity and extra
            # #= *start* gives the star date
            'start': b.start.strftime('%D %I:%M:%S %p'),
            # #= *winner* gives the access to the winner info
            'winner': b.winner.name,
            # #= *n_events* gives the number of events in a Battle
            'n_events': b.events.count(),
            # #= *total_d* gives the total damage of events in a battle
            'total_d': 0 if t_dam is None else t_dam,
            # #= *participants* gives a string with the names of participants with comma between each one
            'participants': p if p != '' else 'None'
        }
        yield d


def fetch_players():
    for p in m.Player.objects.all():
        spells = ', '.join(
            (name+' (In Use)' if use else name for name, use in utils.get_spells(p)))
        d_in = p.events_damage.aggregate(Sum('damage'))['damage__sum']
        d_out = p.events_attack.aggregate(Sum('damage'))['damage__sum']
        d = {
            # Stores data from usual Player entity and extra
            # #= *name* gives the name of the player
            'name': p.name,
            # #= *race* gives the name of the race
            'race': p.race.name,
            # #= *hp* gives the current health points
            'hp': p.hp,
            # #= *weakness* gives the damage type of the player weekness or
            # none if it doesn't have any
            'weakness': p.weakness.name if p.weakness is not None else
            'None',
            # #= *spells* gives the list of knowed spells with the ones in use
            # marked and comma between them
            'spells': 'None' if spells == '' else spells,
            # #= *damage_in* gives the total damage recieved for the player in
            # all his battles
            'damage_in': d_in if d_in is not None else 0,
            # #= *damage_out* gives the total damage made by the player in all
            # his battles
            'damage_out': d_out if d_out is not None else 0,
            # #= *n_battles* gives the number of battles the player
            'n_battles': p.battles.count(),
            # #= *battles_won* gives the number of victories of the player
            'battles_won': p.battles_win.count(),
        }
        yield d


def fetch_beasts():
    for b in m.Beast.objects.all():
        attacks = ', '.join(
            (name for name in utils.get_attacks(b)))
        d_out = b.events_attack.aggregate(Sum('damage'))['damage__sum']
        bat = b.battles.values('pk')
        # faced = m.Player.objects.filter(pk__in=Subquery(bat))
        d = {
            # Stores data from usual Beast entity and extra
            # #= *name* gives the name of the beast
            'name': b.name,
            # #= *race* gives the name of the race
            'race': b.race.name,
            # #= *hp* gives the current health points
            'hp': b.hp,
            # #= *weakness* gives the damage type of the beast weekness or
            # none if it doesn't have any
            'weakness': b.weakness.name if b.weakness is not None else
            'None',
            # #= *attacks* gives the list of knowed attacks comma between them
            'attacks': attacks,
            # #= *damage_out* gives the total damage made by the beast in all
            # his battles
            'damage_out': d_out if d_out is not None else 0,
            # #= *n_battles* gives the number of battles the beast
            'n_battles': bat.count(),
            # #= *n_players* number of players faced by the beast
            'n_players': m.Player.objects.filter(battles_in__pk__in=bat).distinct().count(),
        }
        yield d


def fetch_spells():
    for s in m.Spell.objects.all():
        p_k = s.players.count()
        p_u = m.Player.objects.filter(Q(spell_slot1=s.pk) | Q(spell_slot2=s.pk)
                                      | Q(spell_slot3=s.pk)).count()
        d = {
            # Stores data from usual Spell entity and extra
            # #= *name* gives the name of the spell
            'name': s.name,
            # #= *avg_d* gives the average damage of the spell
            'avg_d': s.average_dmg,
            # #= *type* gives the name of the damage type it deals
            'type': s.type.name,
            # #= *knows* gives the count of all players that knows the spell with
            # a comma between them
            'knows': p_k,
            # #= *uses* gives the count of all players that are using the spell with
            # a comma between them
            'uses': p_u,
            # #= *n_battles* gives the number of battles the spell has been used
            'n_battles': s.events.values('battle').count(),
        }
        yield d


def fetch_home():
    bp = m.Player.objects.annotate(bw=Count('battles_won')).values(
        'bw', 'name').order_by('-bw')[0]
    bb = m.Beast.objects.annotate(bw=Count('battles_won')).values(
        'race__name', 'name', 'bw').order_by('-bw')[0]
    bs = m.Spell.objects.annotate(kw=Count('players_with')).values(
        'name', 'average_dmg', 'kw').order_by('-kw')[0]
    d = {
        # #= *best_player* gives the player with the most battles won
        'best_player': {
            # #= *name* gives the name of the player
            'name': bp['name'],
            # #= *battles* gives the number of battles won
            'battles': bp['bw']
        },
        # #= *best_beast* gives the beast with the most battles won
        'best_beast': {
            # #= *name* gives the name of the beast
            'name': bb['name'],
            # #= *battles* gives the number of battles won
            'battles': bb['bw'],
            # #= *race* gives the name of the race
            'race': bb['race__name']
        },
        # #= *best_spell* gives the spell most known by the players
        'best_spell': {
            # #= *name* gives the name of the spell
            'name': bs['name'],
            # #= *average_d* gives the average damage of the spell
            'average_d': bs['average_dmg'],
            # #= *known* gives the number of players that knows the spell
            'known': bs['kw']
        }
    }
    return d


def home(request):
    return render(request, 'pages/home.html', fetch_home())


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    return render(request, 'pages/contact.html')


def players(request):
    return render(request,
                  'pages/tables_pages/players.html',
                  {'players': (p for p in fetch_players())})


def battles(request):
    return render(request,
                  'pages/tables_pages/battles.html',
                  {'battles': (b for b in fetch_battles())})


def beasts(request):
    return render(request,
                  'pages/tables_pages/beasts.html',
                  {'beasts': (b for b in fetch_beasts())})


def spells(request):
    return render(request,
                  'pages/tables_pages/spells.html',
                  {'spells': (s for s in fetch_spells())})
