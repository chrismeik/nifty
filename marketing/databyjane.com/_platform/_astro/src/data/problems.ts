// <product id="4f1f25e2-da6d-4095-9826-e538b5645fbe">
// Shared by Problems.astro and Experience.astro so every experience item
// lines up with one problem. Keep the two lists in the same order.
// TODO(placeholder): all `experience` text is placeholder until Jane supplies real examples.

export interface Problem {
  id: string;
  title: string;
  problem: string;
  experience: string;
}

export const problems: Problem[] = [
  {
    id: 'state-reporting',
    title: 'State reporting deadlines',
    problem: 'Submissions pile up at the same time every year, and errors surface the week they are due.',
    experience: 'PLACEHOLDER: Prepared and validated state submissions for districts of different sizes, catching errors weeks before the deadline.',
  },
  {
    id: 'sis-errors',
    title: 'SIS data errors',
    problem: 'Duplicate students, missing codes, and mismatched enrollment dates quietly break every report downstream.',
    experience: 'PLACEHOLDER: Cleaned up student information system records and set up simple checks so the same errors do not come back.',
  },
  {
    id: 'attendance',
    title: 'Attendance and chronic absenteeism',
    problem: 'It is hard to see which students are drifting toward chronic absence until it is too late to help.',
    experience: 'PLACEHOLDER: Built attendance and chronic absenteeism tracking that school teams could check weekly.',
  },
  {
    id: 'assessment',
    title: 'Assessment data in too many places',
    problem: 'State tests, interim assessments, and local screeners each live in a different system.',
    experience: 'PLACEHOLDER: Brought assessment results from several systems into one place so teachers could compare them.',
  },
  {
    id: 'dashboards',
    title: 'Dashboards nobody uses',
    problem: 'The district paid for dashboards, but principals and teachers still ask for spreadsheets.',
    experience: 'PLACEHOLDER: Worked with principals to trim dashboards down to the few numbers they actually check.',
  },
  {
    id: 'board-reports',
    title: 'Board reports rebuilt by hand',
    problem: 'Every month someone copies numbers into the same slides and tables from scratch.',
    experience: 'PLACEHOLDER: Automated recurring board reports so they refresh in minutes instead of days.',
  },
];
// </product>
