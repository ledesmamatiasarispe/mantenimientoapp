import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/app_state.dart';
import 'ordenes/ordenes_screen.dart';
import 'equipos/equipos_screen.dart';
import 'repuestos/repuestos_screen.dart';
import 'cronograma/cronograma_screen.dart';
import 'admin/admin_home.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isAdmin = state.tecnico?.esAdmin ?? false;

    final screens = [
      const OrdenesScreen(),
      const EquiposScreen(),
      const RepuestosScreen(),
      const CronogramaScreen(),
      if (isAdmin) const AdminHome(),
    ];

    final destinations = [
      const NavigationDestination(
          icon: Icon(Icons.assignment_outlined),
          selectedIcon: Icon(Icons.assignment),
          label: 'Órdenes'),
      const NavigationDestination(
          icon: Icon(Icons.precision_manufacturing_outlined),
          selectedIcon: Icon(Icons.precision_manufacturing),
          label: 'Equipos'),
      const NavigationDestination(
          icon: Icon(Icons.inventory_2_outlined),
          selectedIcon: Icon(Icons.inventory_2),
          label: 'Repuestos'),
      const NavigationDestination(
          icon: Icon(Icons.calendar_month_outlined),
          selectedIcon: Icon(Icons.calendar_month),
          label: 'Cronograma'),
      if (isAdmin)
        const NavigationDestination(
            icon: Icon(Icons.admin_panel_settings_outlined),
            selectedIcon: Icon(Icons.admin_panel_settings),
            label: 'Admin'),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _index.clamp(0, screens.length - 1),
        children: screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index.clamp(0, destinations.length - 1),
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: destinations,
      ),
    );
  }
}
