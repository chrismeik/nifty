export type SmsSlide = {
  key: string;
  icon: string;
  title: string;
  description: string;
  timestamp: string;
  message: string;
  comingSoon?: boolean;
  image?: string;
  comingSoonStyle?: 'gradient' | 'frosted';
};

export const smsMessages: SmsSlide[] = [
  {
    key: 'unexcused_absence',
    icon: '📬',
    title: 'Unexcused Absence',
    description: "When a student has an unexcused absence, Nifty notifies parents by text — giving them the full picture on their child's attendance and a direct line to the school office.",
    timestamp: 'Today 8:03 AM',
    message: `Liam Espinoza — Unexcused Absence\n10/23/26\n\nPlease contact the school office before 8:30 AM to resolve this, otherwise it will remain unexcused.\n<span class="sms-phone">(913)352-8531</span>\n\n<span class="sms-divider">************************</span>\n\n2026-27 Absences: 5\nUnexcused: 1 · Parent Excused: 3 · Other Excused: 1`,
  },
  {
    key: 'encouragement',
    icon: '💛',
    title: 'Streak Nudge',
    description: "When a student misses time, Nifty sends a warm nudge — acknowledging the absence while encouraging the family to rebuild the streak.",
    timestamp: 'Today 8:03 AM',
    message: `Mia Johnson — Attendance Update\n10/23/26\n\nWe missed Mia this week. We're always glad when she's here — it's time to start building that streak back up!\n\n<span class="sms-divider">************************</span>\n\nCurrent Streak: 3 days\nRecord Streak: 59 days`,
  },
  {
    key: 'trajectory_warning',
    icon: '📊',
    title: 'Early Warning',
    description: "Nifty looks ahead. When a student's trajectory puts them at risk of exhausting excused absences, parents are notified early — before it becomes a crisis.",
    timestamp: 'Today 8:03 AM',
    message: `Henry Garcia — Attendance Alert\n10/23/26\n\nBased on Henry's attendance trajectory, he will be all out of Parent Excused Absences by February. Please contact the attendance secretary for needed support.\n<span class="sms-phone">(913)352-8532</span>\n\n<span class="sms-divider">************************</span>\n\n2026-27 Parent Excused: 8 of 10 used\nUnexcused: 1 · Other Excused: 1`,
  },
  {
    key: 'streak_celebration',
    icon: '🏆',
    title: 'Attendance Streak',
    description: "Nifty doesn't just flag problems. When students build an attendance streak, parents get a celebratory message that keeps the momentum going.",
    timestamp: 'Today 8:03 AM',
    message: `Mia Johnson — Attendance Streak 🏆\n10/23/26\n\nShe is on track to earn an extra recess with perfect or near-perfect attendance for October. Mia keeps rocking her school attendance! 🎸\n\nOnly 5 more days until you break your personal record! Way to go, Mia!!!\n\n<span class="sms-divider">************************</span>\n\nCurrent Streak: 42 days\nRecord Streak: 46 days`,
  },
  {
    key: 'monthly_report',
    icon: '📋',
    title: 'Monthly Report',
    description: "Every month, administrators receive a district-wide attendance summary — including funding impact and annual projections tied to attendance rates.",
    timestamp: 'Today 8:03 AM',
    message: `Springfield R-XII — Monthly Report\nOctober 2026\n\nDistrict Attendance %:\nOctober 25': 91%\nOctober 26': 93%\n\n<span class="sms-divider">************************</span>\n\nIncrease in Funding: $17,453.23\nAnnual Projection: $163,077.42`,
  },
  {
    key: 'truancy_letters',
    icon: '📄',
    title: 'Truancy Letters — Coming Soon!',
    description: "Nifty will track attendance against local rules, auto-generate state-compliant truancy letters, and email them directly to your office staff — no paperwork, no missed notices.",
    timestamp: '',
    message: '',
    comingSoon: true,
    image: '/truancy.png',
    comingSoonStyle: 'gradient',
  },
  {
    key: 'attendance_certificates',
    icon: '🎓',
    title: 'Attendance Certificates — Coming Soon!',
    description: "Reward perfect and improved attendance with printable certificates. Nifty generates them automatically — ready for teachers to hand out at the end of every month, term, or school year.",
    timestamp: '',
    message: '',
    comingSoon: true,
    image: '/certificates.png',
    comingSoonStyle: 'gradient',
  },
  {
    key: 'attendance_reports',
    icon: '📈',
    title: 'Attendance Reports — Coming Soon!',
    description: "A full suite of attendance and ADA funding reports — delivered to your inbox on a schedule you set. Weekly summaries, monthly deep-dives, and year-end projections, all in one place.",
    timestamp: '',
    message: '',
    comingSoon: true,
    image: '/reports.png',
    comingSoonStyle: 'gradient',
  },
];
