# OBPC Design System

Referência visual global baseada no dashboard financeiro aprovado.

## Tokens

- `--obpc-primary`: azul principal.
- `--obpc-success`, `--obpc-danger`, `--obpc-warning`, `--obpc-info`: estados semânticos.
- `--obpc-bg-page`, `--obpc-bg-card`, `--obpc-bg-soft`: superfícies.
- `--obpc-text-primary`, `--obpc-text-secondary`, `--obpc-text-muted`: tipografia.
- `--obpc-border`: bordas.
- `--obpc-radius-*`: raios.
- `--obpc-shadow-*`: profundidade.

## Componentes

- Page shell: `.obpc-page`, `.obpc-page-header`, `.obpc-page-title`, `.obpc-page-subtitle`.
- Cards: `.obpc-card`, `.obpc-chart-card`.
- KPIs: `.obpc-kpi`, `.obpc-kpi--primary`, `.obpc-kpi--success`, `.obpc-kpi--danger`, `.obpc-kpi--warning`, `.obpc-kpi--info`, `.obpc-kpi--neutral`.
- Cards operacionais: `.obpc-ops`.
- Botões: `.obpc-btn`, `.obpc-btn-primary`, `.obpc-btn-secondary`, `.obpc-btn-success`, `.obpc-btn-danger`, `.obpc-btn-warning`, `.obpc-btn-ghost`, `.obpc-btn-icon`.
- Tabelas: `.obpc-table-wrap`, `.obpc-table`, `.obpc-table-actions`.
- Badges: `.obpc-badge`.
- Formulários: `.obpc-form`, `.obpc-field`, `.obpc-label`, `.obpc-input`, `.obpc-select`, `.obpc-textarea`, `.obpc-help`, `.obpc-error`.
- Filtros: `.obpc-filter-bar`.
- Alertas: `.obpc-alert`, `.obpc-alert-success`, `.obpc-alert-warning`, `.obpc-alert-danger`, `.obpc-alert-info`.
- Empty state: `.obpc-empty`, `.obpc-empty-icon`, `.obpc-empty-title`, `.obpc-empty-description`, `.obpc-empty-action`.
- Ações rápidas: `.obpc-quick-actions`, `.obpc-quick-action`.
- Seções: `.obpc-section`, `.obpc-section-header`, `.obpc-section-title`, `.obpc-section-subtitle`, `.obpc-section-actions`.
- Gráficos: `.obpc-chart-card`, `.obpc-chart-header`, `.obpc-chart-body`, `.obpc-chart-legend`.

## Uso

Use o design system como fundação e complemente com `extra_css` apenas para ajustes de página.

```html
<section class="obpc-page">
  <header class="obpc-page-header obpc-page-header--hero">
    <div>
      <h1 class="obpc-page-title"><i class="fa-solid fa-layer-group"></i> Título</h1>
      <p class="obpc-page-subtitle">Descrição curta.</p>
    </div>
  </header>
</section>
```