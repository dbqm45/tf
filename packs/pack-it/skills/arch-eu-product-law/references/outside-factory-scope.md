# Outside the factory's scope — DSA, consumer law, KSeF, ViDA (as of 2026-10-18)

**Outside the factory's scope.** The IT factory deals with law only within the scope of building software, also with AI
(the human's decision of 2026-10-20). The notes below stay as supporting material: the skill does not apply them in the map
of obligations, and you direct a question about these acts to a lawyer, accounting or the product owner. Facts from secondary sources
[secondary] (accessed 2026-10-18), not checked in EUR-Lex or ISAP.

## Rows of the former map of acts
| Act | When it applies | Deadline |
|---|---|---|
| DSA, Reg. (EU) 2022/2065 | content hosting, online platforms | from 17.02.2024 [secondary] |
| Consumer law, Dir. 2011/83/EU with the Omnibus 2019/2161 | B2C online, digital content and services, also "paid with data" | Omnibus from 28.05.2022 [secondary] |
| The withdrawal button, Art. 11a Dir. 2011/83 (Dir. 2023/2673) | B2C contracts concluded online | application 19.06.2026; in PL no transposition (as of 18.10.2026) [secondary] |
| KSeF, the act of 5.08.2025 (Dz.U. 2025 item 1203) | invoices in Poland | 1.02.2026 large, 1.04.2026 the rest; penalties from 1.01.2027 [secondary] |
| ViDA, Dir. (EU) 2025/516 | e-invoices and VAT reporting for B2B within the EU | 1.07.2030 [secondary] |

Former qualifying questions: "Are the customers consumers (B2C)?" → consumer law and the withdrawal button;
"Do you store or publish user content?" → DSA; "Do you issue invoices in Poland or B2B in the EU?" → KSeF, ViDA.
Former gaps in the code: the withdrawal button, content reporting, a justification for an account block, KSeF integration.

## DSA — Reg. (EU) 2022/2065
- Applies from 17.02.2024.
- **Art. 17:** a statement of reasons for the user on restricting content, payments or an account [secondary].
- **Art. 16:** a mechanism for reporting illegal content — the content was not read [unverified].
- **Art. 25:** a ban on manipulative interfaces (dark patterns) for online platform providers; it does not cover
  practices covered by Directive 2005/29/EC or the GDPR [secondary].
- **Art. 19:** micro and small enterprises are exempt from the section on online platforms (apart from Art. 24(3));
  it does not apply to very large platforms (VLOP). Art. 29 is a separate section for marketplaces [secondary].
- **In the code:** a reporting form, a register of moderation decisions with reasons, a review of the interface for
  manipulation (cancelling as easy as signing up).
- Source: springlex.eu (DSA, Art. 19 and 25).

## Consumer law — Dir. 2011/83/EU after the Omnibus (2019/2161)
- Digital content: the consumer loses the right of withdrawal after an express request for immediate delivery and acknowledging
  the loss of the right (Art. 16(m)); for a service the right expires after full performance (Art. 16(a)) [secondary,
  wording [unverified]].
- The directive also covers contracts in which the consumer "pays" with personal data (Art. 3(1a)) [secondary].
- The Omnibus applies from 28.05.2022 [secondary].
- The prior-price rule (Art. 6a Dir. 98/6/EC): the scope for digital services [unverified].
- **The withdrawal button (Art. 11a, added by Dir. 2023/2673):** transposition by 19.12.2025, application from 19.06.2026.
  In Poland no transposition as of 18.10.2026: draft UC82 withdrawn in May 2026, a new draft from the start of the procedure
  [secondary, one source: akademialtca.pl]. Check the state in ISAP before a decision.
- **In the code:** pre-contractual information before payment, confirmation on a durable medium (an email), consent to
  immediate delivery with the loss of the right of withdrawal (a separate field), an online withdrawal function.
- Sources: fieldfisher.com (Omnibus), iubenda.com (right of withdrawal), akademialtca.pl (Dir. 2023/2673).

## KSeF — the act of 5.08.2025 (Dz.U. 2025 item 1203)
- Obligation: from 1.02.2026 taxpayers with sales above PLN 200 million in 2024; from 1.04.2026 the rest.
- Penalties (Art. 106ni of the VAT act): no sanctions until 31.12.2026; from 1.01.2027 [secondary].
- The exemption for sales up to PLN 10 thousand gross a month: sources conflict (until the end of 2026 or otherwise)
  [unverified].
- **In the code:** integration with the KSeF API (sending, the KSeF number on the invoice, receiving purchase invoices), an emergency mode,
  permissions and tokens in the secrets manager.
- Sources: mddp.pl (Tax Alert KSeF 2.0, 2.09.2025), amavat.pl, ksiegowosc.infor.pl.

## ViDA — Dir. (EU) 2025/516
- Published 25.03.2025, in force from 14.04.2025.
- Mandatory e-invoicing and e-reporting of intra-EU B2B transactions from 1.07.2030; harmonization of national
  systems by 2035 [secondary].
- National e-invoices without the recipient's consent and without a Council derogation — the date differs in sources (25.03 or 14.04.2025).
- Sources: kpmg.com (ViDA publication), accountancyeurope.eu.
