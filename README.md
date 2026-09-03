# Top-Fight.cz Google News sitemap

Automaticky generuje `news-sitemap.xml` z nejnovějších článků na https://www.top-fight.cz/ a ponechává jen články publikované v posledních 48 hodinách.

## Nasazení přes GitHub Pages

1. Vytvoř nový veřejný GitHub repozitář, například `topfight-news-sitemap`.
2. Nahraj do něj celý obsah tohoto balíčku včetně složky `.github`.
3. V repozitáři otevři **Settings -> Pages**.
4. U **Build and deployment** zvol **Deploy from a branch**.
5. Branch: `main`, folder: `/ (root)`, potom **Save**.
6. Otevři záložku **Actions** a spusť workflow **Update Top-Fight Google News sitemap** přes **Run workflow**.
7. Po prvním běhu bude veřejná adresa přibližně:
   `https://TVUJ-LOGIN.github.io/topfight-news-sitemap/news-sitemap.xml`
8. V Google Search Console musíš mít ověřený Top-Fight.cz a také vlastnictví hostitelského webu pro cross-site submission. Poté sitemap odešli v přehledu **Sitemaps**.

Workflow běží každých 30 minut a aktualizuje pouze tehdy, když se XML skutečně změnilo.

## Poznámka

Google News sitemap má obsahovat pouze články vytvořené v posledních 2 dnech. XML používá požadované `news:name`, `news:language`, `news:publication_date` a `news:title`.
