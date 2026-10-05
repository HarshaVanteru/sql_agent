/**
 * Questions to offer when someone is not sure what to ask.
 *
 * Grouped by what the conversation is already about. Each group carries a
 * pattern tested against the recent turns -- the last question, the answer,
 * the SQL and the column names that came back -- so a conversation about
 * orders is offered questions about orders, and one that just came back empty
 * is offered ways to find out why.
 *
 * The questions are deliberately generic: this app points at databases nobody
 * here has seen, so anything naming a real table would be wrong more often
 * than right. "Which table has the most rows?" works anywhere.
 */
interface SuggestionGroup {
  /** When these apply. Absent means always -- the openers. */
  when?: RegExp;
  /**
   * How much a match is worth, against groups that also matched. Default 1.
   * Raised for groups that describe a *state* rather than a subject: an answer
   * saying a table is empty is best followed by "which tables have data",
   * whatever the table happened to be about.
   */
  weight?: number;
  questions: readonly string[];
}

const GROUPS: readonly SuggestionGroup[] = [
  {
    // Openers, used before there is any context and to pad a thin match.
    questions: [
      'What tables are in here?',
      'Which table has the most rows?',
      'Show me 10 rows from the largest table',
      'What does this database appear to be for?',
      'Which tables are empty?',
      'How many rows are in each table?',
      'What are the biggest tables by row count?',
      'Show me the column names of every table',
      'Which tables were added most recently?',
      'Give me a summary of what this database holds',
      'What kinds of records are stored here?',
      'Show me a sample row from each of the five largest tables',
      'Which table would you start with to understand this database?',
      'Are there any lookup or reference tables?',
      'What is the total number of rows across all tables?',
      'Which columns appear in more than one table?',
      'Show me anything that looks like a main entity table',
      'What relationships exist between the tables?',
      'Is there anything unusual about how this database is structured?',
      'Show me the ten most recently created records anywhere',
    ],
  },
  {
    when: /\b(counts?|how many|totals?|sum|average|avg|number of)\b/,
    questions: [
      'Break that down by month',
      'What is the average instead of the total?',
      'Show me the same figure for each category',
      'How does that compare to last month?',
      'What are the highest and lowest values?',
      'Show me the top 10 by that count',
      'What percentage of the total is that?',
      'Is that number growing or shrinking over time?',
      'Show me the rows behind that number',
      'Which group contributes the most to that total?',
    ],
  },
  {
    when: /\b(date|time|created|updated|timestamp|recent|month|year|day|expir)/,
    questions: [
      'What is the earliest record in here?',
      'What is the most recent record?',
      'Show me everything created in the last 30 days',
      'How many records were created each month?',
      'Which day had the most activity?',
      'Are there any records with dates in the future?',
      'Show me anything that has expired',
      'What is the gap between the oldest and newest record?',
      'Has the rate of new records changed over time?',
      'Show me records created in the last week, newest first',
      'Which records have not been updated since they were created?',
      'Are there any records with a missing date?',
    ],
  },
  {
    when: /\b(user|customer|account|member|person|people|email|profile)/,
    questions: [
      'How many users are there?',
      'Show me the 10 most recently created users',
      'How many users signed up each month?',
      'Are there any duplicate email addresses?',
      'Which users have the most activity?',
      'How many users have never done anything?',
      'Show me users with incomplete profiles',
      'What is the most common email domain?',
      'Are there any inactive or disabled accounts?',
      'Which users were created first?',
      'How many users are there per role or type?',
      'Show me users that have no related records at all',
    ],
  },
  {
    when: /\b(order|purchase|payment|invoice|transaction|revenue|sale|price|amount|cart|checkout)/,
    questions: [
      'What is the total revenue?',
      'Show me the 10 largest orders',
      'What is the average order value?',
      'How many orders were placed each month?',
      'Which customers have spent the most?',
      'How many orders are still unpaid or pending?',
      'What is the most common order status?',
      'Show me orders with no line items',
      'Which day of the week gets the most orders?',
      'Are there any orders with a zero or negative amount?',
      'What is the revenue trend over the last six months?',
      'Show me the first order ever placed',
    ],
  },
  {
    when: /\b(file|document|upload|storage|attachment|folder|bytes|filesize)/,
    questions: [
      'How much storage is used in total?',
      'Show me the 10 largest files',
      'What file types are most common?',
      'How many files were uploaded each month?',
      'Are there any files with no owner?',
      'Which users are using the most storage?',
      'How many files have more than one version?',
      'Show me files that have never been opened',
    ],
  },
  {
    when: /\b(token|api[_ ]?key|secret|hash|password|credential|auth|session|login|refresh)/,
    questions: [
      'How many of these are still active?',
      'Show me anything that has already expired',
      'Which of these have never been used?',
      'What is the oldest one still in use?',
      'How many were created in the last month?',
      'Which user has the most of these?',
      'Are any of these shared between users?',
      'Show me the most recently used ones',
    ],
  },
  {
    when: /\b(share|permission|access|role|admin|owner|public|private|visibility)/,
    questions: [
      'How many things are shared publicly?',
      'What permission levels exist?',
      'Who shares the most?',
      'Show me shares that have expired',
      'Are there any shares pointing at deleted records?',
      'Which records are shared with the most people?',
      'How many users have admin access?',
      'Show me the most recent shares',
    ],
  },
  {
    when: /\b(employee|department|staff|salar|manager|hire|team|job|title)/,
    questions: [
      'How many employees are in each department?',
      'What is the average salary by department?',
      'Who has been here the longest?',
      'Show me the most recent hires',
      'Which department has grown the most?',
      'Are there any employees without a department?',
      'What is the range of salaries?',
      'Show me the reporting structure',
    ],
  },
  {
    when: /\b(product|item|inventory|stock|sku|catalog|categor|brand)/,
    questions: [
      'How many products are there?',
      'Which products are out of stock?',
      'What are the most expensive products?',
      'How many products are in each category?',
      'Show me products that have never been ordered',
      'What is the average price by category?',
      'Are there any products with no category?',
      'Which products were added most recently?',
    ],
  },
  {
    when: /\b(\w*log|event|activit|audit|history|tracking|analytics)/,
    questions: [
      'What happened most recently?',
      'What is the most common type of event?',
      'How many events were recorded each day?',
      'Which hour of the day is busiest?',
      'Show me anything that looks like an error',
      'Which record has the most events against it?',
      'How far back does this history go?',
      'Are there any gaps in the history?',
    ],
  },
  {
    when: /\b(empty|no rows|0 rows|zero|none|does not exist|nothing|no results?)\b/,
    // Above anything a subject group can reach on a short answer: "no logs to
    // display" says "logs" three times, and answering that with more log
    // questions sends someone back to the same empty table.
    weight: 4,
    questions: [
      'Which tables here actually have data?',
      'Show me a table that is not empty',
      'How many rows are in each table?',
      'What is the largest table I could look at instead?',
      'Is there a similar table with data in it?',
      'Show me the tables with the most rows',
    ],
  },
  {
    when: /\b(null|missing|blank|unknown|not set|incomplete|duplicate)/,
    questions: [
      'Which columns have the most missing values?',
      'How many rows are missing that field?',
      'Show me the rows with missing values',
      'Are there columns that are always null?',
      'Which records look incomplete?',
      'Are there duplicate rows in this table?',
      'Do any values look obviously wrong?',
      'Which columns are always the same value?',
    ],
  },
  {
    when: /\b(join|foreign key|referenc|relation|related|links?|parent|child)|_id\b/,
    questions: [
      'What does this table join to?',
      'Are there any orphaned records?',
      'Show me this joined to the table it references',
      'Which foreign keys point at missing rows?',
      'What is the full set of relationships from here?',
      'Show me one complete record with everything joined in',
      'Which table is referenced the most?',
      'Are there any circular references?',
    ],
  },
  {
    when: /\b(table|schema|column|structure|describe|field|index|primary key|constraint)/,
    questions: [
      'What columns does that table have?',
      'What is the primary key?',
      'Which columns are indexed?',
      'Show me 10 rows from that table',
      'What data types are used here?',
      'Which columns allow nulls?',
      'Are there any unique constraints?',
      'Show me the distinct values in that column',
    ],
  },
];

function shuffled<T>(items: readonly T[]): T[] {
  const pool = [...items];
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j] as T, pool[i] as T];
  }
  return pool;
}

export const SUGGESTION_COUNT = GROUPS.reduce((n, group) => n + group.questions.length, 0);

/** How strongly a group applies: how many words in the context it recognises. */
function score(pattern: RegExp, haystack: string): number {
  const everywhere = new RegExp(pattern.source, pattern.flags.replace('g', '') + 'g');
  return (haystack.match(everywhere) ?? []).length;
}

interface SuggestOptions {
  /** Recent conversation text: the last answer, its SQL, its column names. */
  context?: string;
  /** Questions already asked, so the same one is not offered back. */
  asked?: readonly string[];
  count?: number;
}

/**
 * Questions worth offering next.
 *
 * Groups are ranked by how much of the context they recognise, then drawn from
 * in turn -- one each, best first, round and round. Ranking matters more than
 * it sounds: an answer about orders mentions "recent" once and "order" and
 * "amount" between them three times, and pooling every match equally let the
 * single incidental word supply all three questions. Taking turns keeps the
 * strongest topic in front without making all three the same thing.
 *
 * Openers fill any shortfall, so there are always `count` of them even on a
 * database whose answers match nothing at all.
 */
export function suggestQuestions({ context = '', asked = [], count = 3 }: SuggestOptions = {}): string[] {
  // total_amount, customer_id, created_at: \b does not see a boundary at an
  // underscore, so \bamount never matched the column that names it.
  const haystack = context.toLowerCase().replace(/_/g, ' ');
  const alreadyAsked = new Set(asked.map((question) => question.trim().toLowerCase()));

  const ranked = GROUPS.filter((group) => group.when)
    .map((group) => ({ group, score: score(group.when as RegExp, haystack) * (group.weight ?? 1) }))
    .filter((entry) => entry.score > 0)
    // Ties broken by weight, not by declaration order. They happen easily:
    // a question about access_logs and an answer saying there are none score
    // the same, and whichever group was written first would otherwise win.
    .sort((a, b) => b.score - a.score || (b.group.weight ?? 1) - (a.group.weight ?? 1))
    .map((entry) => shuffled(entry.group.questions));

  const openers = GROUPS.filter((group) => !group.when).flatMap((group) => shuffled(group.questions));

  const usable = (question: string) => !alreadyAsked.has(question.toLowerCase());
  const picked: string[] = [];

  // A turn each, best-scoring group first, until there are enough.
  for (let round = 0; picked.length < count; round += 1) {
    const anyLeft = ranked.some((questions) => questions.length > round);
    if (!anyLeft) break;
    for (const questions of ranked) {
      if (picked.length === count) break;
      const question = questions[round];
      // Groups overlap -- "how many users" is both a count and a user
      // question -- so the same text can come round twice.
      if (question && usable(question) && !picked.includes(question)) picked.push(question);
    }
  }

  for (const question of openers) {
    if (picked.length === count) break;
    if (usable(question) && !picked.includes(question)) picked.push(question);
  }

  return picked;
}
