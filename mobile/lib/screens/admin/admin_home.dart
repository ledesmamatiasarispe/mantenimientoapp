import 'package:flutter/material.dart';
import 'admin_equipos_screen.dart';
import 'admin_tecnicos_screen.dart';
import 'admin_repuestos_screen.dart';
import 'admin_programas_screen.dart';

class AdminHome extends StatelessWidget {
  const AdminHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Administración')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _AdminCard(
            icon: Icons.precision_manufacturing,
            title: 'Equipos',
            subtitle: 'Gestionar equipos y tipos',
            onTap: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => const AdminEquiposScreen())),
          ),
          _AdminCard(
            icon: Icons.engineering,
            title: 'Técnicos',
            subtitle: 'Gestionar técnicos y contraseñas',
            onTap: () => Navigator.push(context,
                MaterialPageRoute(
                    builder: (_) => const AdminTecnicosScreen())),
          ),
          _AdminCard(
            icon: Icons.inventory_2,
            title: 'Repuestos',
            subtitle: 'Gestionar stock de repuestos',
            onTap: () => Navigator.push(context,
                MaterialPageRoute(
                    builder: (_) => const AdminRepuestosScreen())),
          ),
          _AdminCard(
            icon: Icons.calendar_today,
            title: 'Programas de mantenimiento',
            subtitle: 'Gestionar programas y pasos',
            onTap: () => Navigator.push(context,
                MaterialPageRoute(
                    builder: (_) => const AdminProgramasScreen())),
          ),
        ],
      ),
    );
  }
}

class _AdminCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _AdminCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primaryContainer,
          child: Icon(icon,
              color: Theme.of(context).colorScheme.primary),
        ),
        title: Text(title,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
