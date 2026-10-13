// General marketing guidance for advisers. Not compliance or legal advice.
export type TipSection = { id: string; icon: string; title: string; intro?: string; points: string[] };

export const TIP_SECTIONS: TipSection[] = [
  {
    id: "compliance",
    icon: "shield",
    title: "Before you post anything",
    intro: "Ads and social posts about protection are financial promotions. Get them right first.",
    points: [
      "Get every ad, post and landing page approved by your compliance team (or your principal firm if you’re an Appointed Representative) before it goes live. Keep a record of the approval.",
      "Promotions must be fair, clear and not misleading (FCA COBS 4). Show your firm name and FCA status on ads and landing pages.",
      "Read the FCA’s guidance on financial promotions on social media (FG24/1). Each post must work on its own, even if seen without the rest of the thread.",
      "Google requires UK financial services advertisers to complete its FCA authorisation check before ads will run. Allow a few days for this.",
      "Meta (Facebook / Instagram) may ask you to declare a special ad category for financial products, which limits age and location targeting. Check this in Ads Manager.",
    ],
  },
  {
    id: "dos",
    icon: "check-circle",
    title: "Do",
    points: [
      "Lead with the family, not the product: “Would your family be okay?” works better than “Cheap life insurance”.",
      "Be honest about what the app is: a free, five-minute estimate, not advice and not a quote.",
      "Use real, relatable moments: a new baby, a first home, going self-employed.",
      "Make the next step small and safe: “See your result. No sales call unless you ask.”",
      "Use a separate ad link for each campaign so you can see which ones bring in leads.",
    ],
  },
  {
    id: "donts",
    icon: "x-circle",
    title: "Don’t",
    points: [
      "Don’t use fear for its own sake: no funerals, crying children or “Will you die without cover?”. Emotional framing must stay accurate and respectful (Consumer Duty).",
      "Don’t promise prices, savings or outcomes (“cover from £5 a month”, “guaranteed payout”) unless your compliance team approves the exact wording and conditions.",
      "Don’t call the app “advice” or say it recommends products.",
      "Don’t use client stories or testimonials without written consent and compliance approval.",
      "Don’t target people based on health conditions or bereavement.",
    ],
  },
  {
    id: "audiences",
    icon: "users",
    title: "Who to reach",
    points: [
      "New and expecting parents (25–40). The strongest trigger for protection.",
      "Recent home buyers and people remortgaging: a bigger mortgage means a bigger gap.",
      "Self-employed people and contractors, who often have no sick pay or death-in-service cover.",
      "Couples who’ve just married or moved in together.",
      "Your existing clients: ask them to share with friends (a referral is the warmest lead there is).",
    ],
  },
  {
    id: "copy",
    icon: "edit-3",
    title: "Ad wording ideas",
    intro: "Starting points only. Have your compliance team approve the final wording.",
    points: [
      "“If you couldn’t work tomorrow, how long would your family’s money last? Find out in 5 minutes.”",
      "“You’ve planned the nursery. Have you planned for the unexpected? A gentle 5-minute check.”",
      "“New home, new mortgage. Would your family be able to stay there? See your free estimate.”",
      "“Self-employed? No sick pay means your savings are your safety net. See how long they’d last.”",
      "“Most families never ask the question. This free app answers it gently. No sales call unless you ask.”",
    ],
  },
  {
    id: "budget",
    icon: "trending-up",
    title: "Budgets & testing",
    points: [
      "Start small: £5–£10 a day on one platform, with 2–3 ad versions running at once.",
      "Run each test for at least 7–14 days before judging it. Early results swing a lot.",
      "Judge ads on cost per lead (call-back request), not clicks or likes.",
      "Pause the weakest version each week and try a new one against the winner.",
      "Facebook and Instagram suit parents and life events. Google search catches people already looking (e.g. “life insurance for new parents”).",
    ],
  },
  {
    id: "free",
    icon: "heart",
    title: "Free ways to get leads",
    points: [
      "Send the app to every client after a review using Invite a client.",
      "Partner with local estate agents, mortgage brokers and solicitors (with your firm’s agreement).",
      "Use flyers with a QR code and the FLYER ad link at baby groups, nurseries or community events, where you have permission.",
      "Post on LinkedIn about real-life protection gaps, once your compliance team has approved the posts.",
      "Check your dashboard each month to see which sources bring leads that turn into clients.",
    ],
  },
];
