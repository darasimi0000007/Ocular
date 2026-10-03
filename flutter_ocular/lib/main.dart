import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'api.dart';

// ---------- design tokens ----------
const bg = Color(0xFF0B1020), panel = Color(0xFF151B30), accent = Color(0xFF4F6BFF), violet = Color(0xFF8A5CFF);
const brand = LinearGradient(colors: [accent, violet], begin: Alignment.topLeft, end: Alignment.bottomRight);
final navKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Api.loadToken();
  Api.onUnauthorized = () => navKey.currentState
      ?.pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (_) => false);
  runApp(const OcularApp());
}

class OcularApp extends StatelessWidget {
  const OcularApp({super.key});
  @override
  Widget build(BuildContext context) {
    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14));
    return MaterialApp(
      title: 'Ocular',
      navigatorKey: navKey,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorSchemeSeed: accent,
        scaffoldBackgroundColor: bg,
        appBarTheme: const AppBarTheme(backgroundColor: Colors.transparent, elevation: 0),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: panel,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
        ),
        filledButtonTheme: FilledButtonThemeData(
            style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(54), shape: shape,
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600))),
        outlinedButtonTheme: OutlinedButtonThemeData(
            style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(54), shape: shape)),
      ),
      home: Api.token == null ? const LoginScreen() : const HomeScreen(),
    );
  }
}

// ---------- shared widgets ----------
Widget logo([double s = 64]) => Container(
    width: s, height: s,
    decoration: BoxDecoration(gradient: brand, borderRadius: BorderRadius.circular(s / 3.2)),
    child: Icon(Icons.remove_red_eye_rounded, size: s * .5, color: Colors.white));

// full-screen gradient layout used by Login + Signup
Widget authShell(String title, String sub, List<Widget> kids, {bool back = false}) => Scaffold(
      extendBodyBehindAppBar: true,
      appBar: back ? AppBar() : null,
      body: Container(
        decoration: const BoxDecoration(
            gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter,
                colors: [Color(0xFF1B2A6B), bg], stops: [0, .55])),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const SizedBox(height: 24),
              Align(alignment: Alignment.centerLeft, child: logo()),
              const SizedBox(height: 20),
              Text(title, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              Text(sub, style: const TextStyle(color: Colors.white60)),
              const SizedBox(height: 28),
              for (final k in kids) Padding(padding: const EdgeInsets.only(bottom: 14), child: k),
            ]),
          ),
        ),
      ),
    );

// inner-screen layout
Widget page(String title, List<Widget> kids) => Scaffold(
      appBar: AppBar(title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700))),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 8, 20, 24), children: [
          for (final k in kids) Padding(padding: const EdgeInsets.only(bottom: 14), child: k)
        ]),
      ),
    );

Widget field(TextEditingController c, String label, IconData icon, {bool obscure = false, TextInputType? type}) =>
    TextField(controller: c, obscureText: obscure, keyboardType: type,
        decoration: InputDecoration(labelText: label, prefixIcon: Icon(icon)));

void toast(BuildContext c, String m) =>
    ScaffoldMessenger.of(c).showSnackBar(SnackBar(content: Text(m), behavior: SnackBarBehavior.floating));

mixin Busy<T extends StatefulWidget> on State<T> {
  bool busy = false;
  Future<void> run(Future<void> Function() job) async {
    setState(() => busy = true);
    try {
      await job();
    } catch (e) {
      if (mounted) toast(context, e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget btn(String label, VoidCallback onTap) => FilledButton(
      onPressed: busy ? null : onTap,
      child: busy
          ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.5))
          : Text(label));
}

// ---------- Login ----------
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginState();
}

class _LoginState extends State<LoginScreen> with Busy {
  final email = TextEditingController(), pw = TextEditingController();

  @override
  Widget build(BuildContext context) => authShell('Welcome back', 'Sign in to manage attendance', [
        field(email, 'Email', Icons.mail_outline, type: TextInputType.emailAddress),
        field(pw, 'Password', Icons.lock_outline, obscure: true),
        btn('Log in', () => run(() async {
              await Api.login(email.text.trim(), pw.text);
              if (mounted) {
                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const HomeScreen()));
              }
            })),
        TextButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SignupScreen())),
            child: const Text('New organization? Create an account')),
      ]);
}

// ---------- Signup ----------
class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});
  @override
  State<SignupScreen> createState() => _SignupState();
}

class _SignupState extends State<SignupScreen> with Busy {
  static const _f = [
    ('first_name', 'First name', Icons.person_outline),
    ('last_name', 'Last name', Icons.person_outline),
    ('organization_name', 'Organization name', Icons.apartment),
    ('organization_slug', 'Slug, e.g. riverside-academy', Icons.link),
    ('email', 'Email', Icons.mail_outline),
    ('password', 'Password (8+ chars, letter + digit)', Icons.lock_outline),
  ];
  late final c = {for (final f in _f) f.$1: TextEditingController()};

  @override
  Widget build(BuildContext context) => authShell('Create your organization', 'Set up Ocular for your school or company', [
        for (final f in _f)
          field(c[f.$1]!, f.$2, f.$3, obscure: f.$1 == 'password', type: f.$1 == 'email' ? TextInputType.emailAddress : null),
        btn('Sign up', () => run(() async {
              await Api.signup({for (final e in c.entries) e.key: e.value.text.trim()}..['password'] = c['password']!.text);
              if (mounted) {
                toast(context, 'Organization created. Please log in.');
                Navigator.pop(context);
              }
            })),
      ], back: true);
}

// ---------- Home ----------
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  Widget card(BuildContext c, IconData i, String t, String s, Widget dest) => Material(
        color: panel, borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => Navigator.push(c, MaterialPageRoute(builder: (_) => dest)),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(i, color: accent, size: 30),
              const SizedBox(height: 14),
              Text(t, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 2),
              Text(s, style: const TextStyle(fontSize: 12, color: Colors.white54)),
            ]),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: ListView(padding: const EdgeInsets.all(20), children: [
            Row(children: [
              logo(44),
              const SizedBox(width: 12),
              const Expanded(child: Text('Ocular', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800))),
              IconButton(
                  icon: const Icon(Icons.logout),
                  onPressed: () async {
                    await Api.logout();
                    if (context.mounted) {
                      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
                    }
                  }),
            ]),
            const SizedBox(height: 24),
            Material(
              color: Colors.transparent,
              child: Ink(
                decoration: BoxDecoration(gradient: brand, borderRadius: BorderRadius.circular(24)),
                child: InkWell(
                  borderRadius: BorderRadius.circular(24),
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CaptureScreen(enroll: false))),
                  child: const Padding(
                    padding: EdgeInsets.all(24),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Icon(Icons.center_focus_strong, size: 40, color: Colors.white),
                      SizedBox(height: 40),
                      Text('Take attendance', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
                      Text('Scan a face to identify who is present', style: TextStyle(color: Colors.white70)),
                    ]),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(child: card(context, Icons.person_add_alt_1, 'Register person', 'Add & enroll a face', const AddPersonScreen())),
              const SizedBox(width: 14),
              Expanded(child: card(context, Icons.email_outlined, 'Export', 'CSV to your email', const ExportScreen())),
            ]),
            const SizedBox(height: 14),
            card(context, Icons.admin_panel_settings_outlined, 'Add moderator', 'Invite someone to your organization', const AddModeratorScreen()),
          ]),
        ),
      );
}

// ---------- Register person (details -> photo). The person_id is never shown. ----------
class AddPersonScreen extends StatefulWidget {
  const AddPersonScreen({super.key});
  @override
  State<AddPersonScreen> createState() => _AddPersonState();
}

class _AddPersonState extends State<AddPersonScreen> with Busy {
  final ext = TextEditingController(), first = TextEditingController(), last = TextEditingController();

  @override
  Widget build(BuildContext context) => page('Register person', [
        const Text('Step 1 of 2 · Details', style: TextStyle(color: Colors.white54)),
        field(ext, 'ID (matric no. / staff ID)', Icons.badge_outlined),
        field(first, 'First name', Icons.person_outline),
        field(last, 'Last name', Icons.person_outline),
        btn('Continue to photo', () => run(() async {
              final id = await Api.createPerson(ext.text.trim(), first.text.trim(), last.text.trim());
              if (mounted) {
                Navigator.pushReplacement(context, MaterialPageRoute(
                    builder: (_) => CaptureScreen(enroll: true, personId: id, name: '${first.text.trim()} ${last.text.trim()}')));
              }
            })),
      ]);
}

// ---------- Capture (enroll + recognize) ----------
class CaptureScreen extends StatefulWidget {
  final bool enroll;
  final String? personId, name;
  const CaptureScreen({super.key, required this.enroll, this.personId, this.name});
  @override
  State<CaptureScreen> createState() => _CaptureState();
}

class _CaptureState extends State<CaptureScreen> with Busy {
  XFile? shot;
  Map? result;

  Future<void> pick(ImageSource s) async {
    final f = await ImagePicker().pickImage(source: s, maxWidth: 1280, imageQuality: 85);
    if (f != null) setState(() { shot = f; result = null; });
  }

  @override
  Widget build(BuildContext context) {
    final done = widget.enroll && result?['status'] == 'Enrolled Face!';
    return page(widget.enroll ? 'Enroll ${widget.name}' : 'Take attendance', [
      if (widget.enroll) const Text('Step 2 of 2 · Photo', style: TextStyle(color: Colors.white54)),
      Container(
        height: 320,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
            color: panel, borderRadius: BorderRadius.circular(24),
            border: Border.all(color: accent.withValues(alpha: .4), width: 2)),
        child: shot == null
            ? const Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(Icons.face_retouching_natural, size: 72, color: Colors.white38),
                SizedBox(height: 10),
                Text('Center the face in good light', style: TextStyle(color: Colors.white54)),
              ])
            : Image.file(File(shot!.path), fit: BoxFit.cover, width: double.infinity),
      ),
      Row(children: [
        Expanded(child: OutlinedButton.icon(onPressed: () => pick(ImageSource.camera), icon: const Icon(Icons.camera_alt_outlined), label: const Text('Camera'))),
        const SizedBox(width: 12),
        Expanded(child: OutlinedButton.icon(onPressed: () => pick(ImageSource.gallery), icon: const Icon(Icons.photo_outlined), label: const Text('Gallery'))),
      ]),
      if (!done)
        btn(widget.enroll ? 'Enroll face' : 'Recognize', () => run(() async {
              if (shot == null) throw ApiException('Take or choose a photo first');
              final taskId = widget.enroll
                  ? await Api.enroll(widget.personId!, shot!.path)
                  : await Api.recognize(shot!.path);
              final r = await Api.pollTask(taskId);
              setState(() => result = r);
            })),
      AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          child: result == null ? const SizedBox.shrink() : ResultCard(result!, widget.name, key: ValueKey(result))),
      if (done) FilledButton(onPressed: () => Navigator.popUntil(context, (r) => r.isFirst), child: const Text('Done')),
    ]);
  }
}

// turns raw backend statuses into friendly messages
class ResultCard extends StatelessWidget {
  final Map r;
  final String? name;
  const ResultCard(this.r, this.name, {super.key});

  @override
  Widget build(BuildContext context) {
    final s = r['status'];
    IconData icon;
    Color col;
    String t, sub;
    if (s == 'matched') {
      icon = Icons.check_circle; col = Colors.greenAccent;
      t = '${r['first_name']} ${r['last_name']}';
      sub = 'Recognized · ${((r['similarity'] as num) * 100).round()}% match';
    } else if (s == 'Enrolled Face!') {
      icon = Icons.check_circle; col = Colors.greenAccent;
      t = '${name ?? 'Person'} enrolled';
      sub = 'Face saved successfully';
    } else if (s == 'sent') {
      icon = Icons.mark_email_read_outlined; col = Colors.greenAccent;
      t = 'Export sent';
      sub = '${r['count']} records emailed to you';
    } else if (s == 'nothing_to_export') {
      icon = Icons.inbox_outlined; col = Colors.white70;
      t = 'Nothing to export';
      sub = 'No attendance older than 24 hours yet';
    } else if (s == 'no_face_detected') {
      icon = Icons.face_retouching_off; col = Colors.orangeAccent;
      t = 'No face detected';
      sub = 'Retake the photo facing the camera in better light';
    } else {
      icon = Icons.help_outline; col = Colors.redAccent;
      t = 'No match';
      sub = (r['reason'] ?? 'This face is not enrolled') as String;
    }
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
          color: panel, borderRadius: BorderRadius.circular(20),
          border: Border.all(color: col.withValues(alpha: .5))),
      child: Row(children: [
        Icon(icon, size: 40, color: col),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(t, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 2),
          Text(sub, style: const TextStyle(color: Colors.white60)),
        ])),
      ]),
    );
  }
}

// ---------- Export ----------
class ExportScreen extends StatefulWidget {
  const ExportScreen({super.key});
  @override
  State<ExportScreen> createState() => _ExportState();
}

class _ExportState extends State<ExportScreen> with Busy {
  Map? result;

  @override
  Widget build(BuildContext context) => page('Export attendance', [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(20)),
          child: const Row(children: [
            Icon(Icons.description_outlined, color: accent, size: 32),
            SizedBox(width: 14),
            Expanded(child: Text('Emails a CSV of attendance older than 24 hours to your account.', style: TextStyle(color: Colors.white70))),
          ]),
        ),
        btn('Export & email', () => run(() async {
              final r = await Api.pollTask(await Api.exportAttendance());
              setState(() => result = r);
            })),
        if (result != null) ResultCard(result!, null),
      ]);
}

// ---------- Add moderator ----------
class AddModeratorScreen extends StatefulWidget {
  const AddModeratorScreen({super.key});
  @override
  State<AddModeratorScreen> createState() => _AddModState();
}

class _AddModState extends State<AddModeratorScreen> with Busy {
  final slug = TextEditingController(), first = TextEditingController(), last = TextEditingController(),
      email = TextEditingController(), pw = TextEditingController();

  @override
  void initState() {
    super.initState();
    Api.savedSlug().then((s) => slug.text = s ?? '');
  }

  @override
  Widget build(BuildContext context) => page('Add moderator', [
        field(slug, 'Organization slug', Icons.link),
        field(first, 'First name', Icons.person_outline),
        field(last, 'Last name', Icons.person_outline),
        field(email, 'Email', Icons.mail_outline, type: TextInputType.emailAddress),
        field(pw, 'Password', Icons.lock_outline, obscure: true),
        btn('Add moderator', () => run(() async {
              await Api.addModerator(slug.text.trim(), {
                'first_name': first.text.trim(), 'last_name': last.text.trim(),
                'organization_name': slug.text.trim(), 'organization_slug': slug.text.trim(),
                'email': email.text.trim(), 'password': pw.text,
              });
              if (mounted) { toast(context, 'Moderator added'); Navigator.pop(context); }
            })),
      ]);
}
