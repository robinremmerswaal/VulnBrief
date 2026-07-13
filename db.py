{% extends "base.html" %}
{% block title %}Briefings — VulnBrief{% endblock %}
{% block content %}
<h1>Briefings</h1>
<p class="subtitle">Geschiedenis van alle gegenereerde briefings.</p>

<div class="card">
  {% if briefings %}
  <table>
    <thead><tr><th>Client</th><th>Gegenereerd op</th><th></th></tr></thead>
    <tbody>
      {% for b in briefings %}
      <tr>
        <td>{{ b.client_name }}</td>
        <td class="helptext">{{ b.generated_at[:16].replace('T', ' ') }}</td>
        <td><a href="/briefings/{{ b.id }}" class="btn btn-small btn-secondary">Bekijken →</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">Nog geen briefings gegenereerd. Ga naar een client en klik op "Briefing genereren".</div>
  {% endif %}
</div>
{% endblock %}
