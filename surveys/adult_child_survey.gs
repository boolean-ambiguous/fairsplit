/**
 * Digital Stewardship study — ADULT-CHILD segment questionnaire.
 *
 * HOW TO USE
 * 1. Go to https://script.google.com, create a new project, and paste this
 *    entire file in (replacing the default Code.gs contents).
 * 2. Set the FRAME constant below to 'A' or 'B' (see note under FRAME).
 * 3. Select the function `createAdultChildSurveyForm` in the toolbar and
 *    click Run. Authorize the script when prompted.
 * 4. Open the Execution log (View > Logs) for the URL of the created form
 *    and its edit URL. The form is created in your Google Drive.
 * 5. Repeat with FRAME = 'B' (running the function again) to produce the
 *    second framing copy, then split recruitment links 50/50 between the
 *    two copies to realise the between-subjects framing manipulation.
 *
 * LIMITATIONS OF GOOGLE FORMS FOR THIS DESIGN (see also the research notes
 * in the source brief): Google Forms cannot randomly assign respondents to
 * a condition at load time, and it cannot randomise the order of items
 * across sections. Two consequences follow, both documented here rather
 * than silently worked around:
 *   - Framing (FRAME) is fixed per generated form copy, not randomised
 *     per respondent. Running this script twice (FRAME='A' then 'B') and
 *     distributing both links with equal effort approximates random
 *     assignment at the recruitment level, but is not equivalent to
 *     server-side per-respondent randomisation.
 *   - The six scenarios are presented in a FIXED order (1-6) below, not
 *     randomised per respondent. If order effects are a concern, either
 *     accept this as a limitation of the Forms pilot, or generate extra
 *     copies with the scenario order shuffled by hand and split traffic
 *     across those copies too.
 *   - Segment quotas (roughly 100-130 per segment) and the compound
 *     S1/S2 screening rule (age range AND self-reported segment) are not
 *     enforceable natively; Forms can only branch on a single answer at a
 *     time. Monitor response counts manually and clean out age/segment
 *     mismatches during analysis.
 * For a fielded study, a platform with native randomisation (Qualtrics,
 * SurveyMonkey) remains the right tool; this script is provided so the
 * instrument can also be piloted or reviewed in Google Forms.
 */

// ---- Configuration -------------------------------------------------------

var FRAME = 'A'; // 'A' = safe independence, 'B' = family oversight

var FRAME_SENTENCES = {
  A: 'The bank presents this as a way to keep banking on your parent\'s own, confidently and safely, with a trusted person as a backstop.',
  B: 'The bank presents this as a way for the family to keep an eye on the account and step in if something looks wrong.'
};

var RESEARCHER_CONTACT = '[researcher name and email]';

// ---- Helpers ---------------------------------------------------------

function addScale7_(form, title) {
  return form.addScaleItem()
    .setTitle(title)
    .setBounds(1, 7)
    .setLabels('Strongly disagree', 'Strongly agree')
    .setRequired(true);
}

function addOpenNumeric_(form, title, opts) {
  opts = opts || {};
  var item = form.addTextItem().setTitle(title).setRequired(opts.required !== false);
  var validation = FormApp.createTextValidation().requireNumber();
  item.setValidation(validation.build());
  if (opts.helpText) item.setHelpText(opts.helpText);
  return item;
}

function addOpenText_(form, title, opts) {
  opts = opts || {};
  var item = form.addParagraphTextItem().setTitle(title).setRequired(!!opts.required);
  if (opts.helpText) item.setHelpText(opts.helpText);
  return item;
}

// ---- Main builder ----------------------------------------------------

function createAdultChildSurveyForm() {
  var form = FormApp.create('Digital Stewardship Survey — Adult-Child Segment (Framing ' + FRAME + ')');
  form.setDescription(
    'Thank you for taking part in this short study on banking services that help ' +
    'people manage their money safely. This survey is part of a Master\'s thesis at ' +
    'the University of Zurich. It takes about ten to twelve minutes.\n\n' +
    'Your participation is voluntary, your answers are anonymous, and you may stop ' +
    'at any time. The data are processed in accordance with the revised Federal Act ' +
    'on Data Protection and are used only for this research.'
  );
  form.setCollectEmail(false);
  form.setProgressBar(true);
  form.setShuffleQuestions(false);
  form.setIsQuiz(false);

  // ---- Block 0. Welcome and consent ----
  // C0
  var c0 = form.addMultipleChoiceItem()
    .setTitle('I have read the above and agree to take part.')
    .setRequired(true);

  // ---- Block 1. Screening ----
  form.addPageBreakItem().setTitle('Screening');
  // S1
  addOpenNumeric_(form, 'What is your age?', { helpText: 'In years.' });
  // S2
  var s2 = form.addMultipleChoiceItem()
    .setTitle('Which of the following best describes you?')
    .setRequired(true);
  s2.setChoiceValues([
    'I am aged 55 or older and manage at least some of my own banking.',
    'I have a parent or close older relative aged about 65 or older who manages at least some of their own money.',
    'Neither of these.'
  ]);

  // ---- Block 3. Base service description ----
  var basePage = form.addPageBreakItem().setTitle('About the service');
  form.addSectionHeaderItem()
    .setTitle('Digital Stewardship')
    .setHelpText(
      'Imagine your parent\'s bank offers a new service called Digital Stewardship. ' +
      'With this service your parent keeps full control of their account and ' +
      'continues to make payments exactly as they do now. Your parent can choose a ' +
      'trusted person, such as you, to help protect them against fraud. The chosen ' +
      'person can never make or stop a payment. What that person can see and what ' +
      'the service does depend on the settings, which are described in each scenario ' +
      'below.'
    );

  // Screen-out page for ineligible respondents. Its position in the form
  // doesn't matter — branching items below jump to it directly regardless
  // of where eligible respondents go instead. Its text is set near the
  // bottom, once all the branching items that reference it are wired up.
  var screenOutPage = form.addPageBreakItem().setTitle('Thank you');

  // ---- Block 4. Scenarios ----
  var frameSentence = FRAME_SENTENCES[FRAME];

  var scenarios = [
    {
      code: 'monitoring / alerts-only',
      body: 'In this version, you see only alerts, not your parent\'s account ' +
        'details, and you are alerted if something unusual happens. You can never ' +
        'make or stop a payment.'
    },
    {
      code: 'monitoring / balances-and-categories',
      body: 'In this version, you can see your parent\'s account balances and the ' +
        'general types of their spending, but not their individual payments, and you ' +
        'are alerted if something unusual happens. You can never make or stop a ' +
        'payment.'
    },
    {
      code: 'monitoring / full-detail',
      body: 'In this version, you can see your parent\'s full transaction details ' +
        'and you are alerted if something unusual happens. You can never make or ' +
        'stop a payment.'
    },
    {
      code: 'confirmation / alerts-only',
      body: 'In this version, you see only alerts, not your parent\'s account ' +
        'details, and you are alerted if something unusual happens. In addition, for ' +
        'certain high-risk payments the payment pauses briefly so a possible scam can ' +
        'be caught before the money leaves your parent\'s account. You can never make ' +
        'or stop a payment yourself.'
    },
    {
      code: 'confirmation / balances-and-categories',
      body: 'In this version, you can see your parent\'s account balances and the ' +
        'general types of their spending, but not their individual payments, and you ' +
        'are alerted if something unusual happens. In addition, for certain high-risk ' +
        'payments the payment pauses briefly so a possible scam can be caught before ' +
        'the money leaves your parent\'s account. You can never make or stop a payment ' +
        'yourself.'
    },
    {
      code: 'confirmation / full-detail',
      body: 'In this version, you can see your parent\'s full transaction details ' +
        'and you are alerted if something unusual happens. In addition, for certain ' +
        'high-risk payments the payment pauses briefly so a possible scam can be ' +
        'caught before the money leaves your parent\'s account. You can never make or ' +
        'stop a payment yourself.'
    }
  ];

  for (var i = 0; i < scenarios.length; i++) {
    var n = i + 1;
    var sc = scenarios[i];
    form.addPageBreakItem().setTitle('Scenario ' + n + ' of 6');
    form.addSectionHeaderItem()
      .setTitle('Scenario ' + n)
      .setHelpText(frameSentence + '\n\n' + sc.body);
    // BI1
    addScale7_(form, 'If my parent\'s bank offered this version, I would encourage my parent to use it.');
    // BI2
    addScale7_(form, 'I would recommend that my parent sign up for this version.');
    // WTP
    addOpenNumeric_(
      form,
      'What is the most you would be willing to pay per month for this version? ' +
      'Please enter an amount in Swiss francs.',
      { helpText: 'Enter 0 if you would not pay anything. CHF per month.' }
    );
  }

  // ---- Block 5. Manipulation check ----
  form.addPageBreakItem().setTitle('A few more questions about the service');
  form.addSectionHeaderItem().setTitle('Thinking about the service you read about across the scenarios:');
  // MC1
  addScale7_(form, 'The service was described mainly as a way to keep banking independently and safely.');
  // MC2
  addScale7_(form, 'The service was described mainly as a way for family to watch over the account.');

  // ---- Block 6. Acceptance (UTAUT2) ----
  form.addPageBreakItem().setTitle('Your views on the service');
  form.addSectionHeaderItem().setTitle('Thinking about the Digital Stewardship service in general, how much do you agree with each statement?');
  // Performance expectancy: PE1-PE3
  addScale7_(form, 'This service would help my parent avoid financial fraud.');
  addScale7_(form, 'This service would be useful for keeping my parent\'s money safe.');
  addScale7_(form, 'Using this service would make my parent feel more secure about their banking.');
  // Effort expectancy: EE1-EE2
  addScale7_(form, 'Learning to use this service would be easy for my parent.');
  addScale7_(form, 'My parent would find this service easy to use.');
  // Social influence: SI1-SI3
  addScale7_(form, 'People who are important to my parent would think my parent should use this service.');
  addScale7_(form, 'My parent\'s family would approve of using this service.');
  addScale7_(form, 'Most people my parent respects would consider using a service like this.');
  // Price value: PV1-PV3
  addScale7_(form, 'At a reasonable price, this service would be good value for money.');
  addScale7_(form, 'The benefits of this service would justify its cost.');
  addScale7_(form, 'At the price my parent would expect, this service would be worth it.');

  // ---- Block 7. Independence and self-image ----
  form.addPageBreakItem().setTitle('Independence');
  form.addSectionHeaderItem().setTitle('Still thinking about the service in general, how much do you agree with each statement?');
  // IT1-IT3
  addScale7_(form, 'Using this service would make my parent feel less independent.');
  addScale7_(form, 'Accepting this service would feel like admitting my parent can no longer manage alone.');
  addScale7_(form, 'Using this service would feel like a loss of my parent\'s independence.');

  // ---- Block 8. Background and controls ----
  form.addPageBreakItem().setTitle('About you');
  // C1
  addScale7_(form, 'I am confident using online or mobile banking.');
  // C1b (adult-child segment only)
  addScale7_(form, 'My parent is confident using online or mobile banking.');
  // C2
  var c2 = form.addMultipleChoiceItem()
    .setTitle('Have you, or someone close to you, ever been the target of a financial scam or fraud?')
    .setChoiceValues(['Yes', 'No', 'Prefer not to say'])
    .setRequired(true);

  // Page shown only if C2 = Yes
  var c2bPage = form.addPageBreakItem().setTitle('Optional follow-up');
  // C2b
  addOpenText_(
    form,
    'If you are comfortable sharing, what happened?',
    { required: false, helpText: 'Optional — you may leave this blank.' }
  );

  // Page for respondents who skip C2b
  var afterC2Page = form.addPageBreakItem().setTitle('A few last questions');
  // D1 (adult-child segment only)
  addOpenNumeric_(form, 'Approximately how old is the parent you had in mind?', { helpText: 'In years.' });
  // D2
  var d2 = form.addMultipleChoiceItem()
    .setTitle('Gender')
    .setChoiceValues(['Female', 'Male', 'Other', 'Prefer not to say'])
    .setRequired(false);
  // D3
  addOpenText_(form, 'Highest level of education completed', { required: false });

  // ---- Block 9. Debrief and close ----
  form.addPageBreakItem().setTitle('Thank you');
  form.addSectionHeaderItem()
    .setTitle('Thank you for your answers.')
    .setHelpText(
      'To explain the study: different participants saw the same service described ' +
      'in slightly different ways, so that we can study how the way a service is ' +
      'presented affects people\'s reactions. Digital Stewardship is a research ' +
      'concept and is not currently offered by any bank.\n\n' +
      'If you have any questions about the study, please contact ' + RESEARCHER_CONTACT +
      '. Please click submit to record your responses.'
    );

  // ---- Now wire up branching (all target pages exist by this point) ----

  // C0: "Yes" continues into the screening block; "No" exits immediately.
  screenOutPage.setHelpText(
    'Thank you for your interest. Based on your answer you are not able to take ' +
    'part in this survey. No responses have been recorded.'
  );
  c0.setChoices([
    c0.createChoice('Yes, begin the survey.', FormApp.PageNavigationType.CONTINUE),
    c0.createChoice('No (exit the survey).', screenOutPage)
  ]);

  // S2: only the ADULT-CHILD-matching option continues to the base
  // description; the other two options exit (this is the adult-child
  // segment survey copy).
  s2.setChoices([
    s2.createChoice(
      'I am aged 55 or older and manage at least some of my own banking.',
      screenOutPage
    ),
    s2.createChoice(
      'I have a parent or close older relative aged about 65 or older who manages at least some of their own money.',
      basePage
    ),
    s2.createChoice('Neither of these.', screenOutPage)
  ]);

  // C2: "Yes" continues to the optional follow-up (C2b); the other answers
  // skip straight past it.
  c2.setChoices([
    c2.createChoice('Yes', FormApp.PageNavigationType.CONTINUE),
    c2.createChoice('No', afterC2Page),
    c2.createChoice('Prefer not to say', afterC2Page)
  ]);

  Logger.log('Form created: %s', form.getEditUrl());
  Logger.log('Live link: %s', form.getPublishedUrl());
  return form;
}
