import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/api_client.dart';
import 'core/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final client = ApiClient();
  await client.init();
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(client),
      child: const MantenimientoApp(),
    ),
  );
}

class MantenimientoApp extends StatelessWidget {
  const MantenimientoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Gestión Mantenimiento',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0E6B52),
        ),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0E6B52),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: Consumer<AppState>(
        builder: (context, state, _) =>
            state.isLoggedIn ? const HomeScreen() : const LoginScreen(),
      ),
    );
  }
}
