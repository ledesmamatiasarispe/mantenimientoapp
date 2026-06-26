package com.example.mantenimientoapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.mantenimientoapp.ui.admin.alertas.AlertasScreen
import com.example.mantenimientoapp.ui.admin.dashboard.DashboardScreen
import com.example.mantenimientoapp.ui.admin.equipos.EquiposAdminScreen
import com.example.mantenimientoapp.ui.admin.generar.GenerarOrdenesScreen
import com.example.mantenimientoapp.ui.admin.historial.HistorialEquipoScreen
import com.example.mantenimientoapp.ui.admin.programas.ProgramasAdminScreen
import com.example.mantenimientoapp.ui.admin.proveedores.ProveedoresAdminScreen
import com.example.mantenimientoapp.ui.admin.repuestos.ConsolidadoRepuestosScreen
import com.example.mantenimientoapp.ui.admin.repuestos.RepuestoProveedoresScreen
import com.example.mantenimientoapp.ui.admin.repuestos.RepuestosAdminScreen
import com.example.mantenimientoapp.ui.admin.repuestos.RepuestosEquipoScreen
import com.example.mantenimientoapp.ui.admin.tecnicos.TecnicosAdminScreen
import com.example.mantenimientoapp.ui.auth.LoginScreen
import com.example.mantenimientoapp.ui.home.HomeScreen
import com.example.mantenimientoapp.ui.ordenes.OrdenDetailScreen
import com.example.mantenimientoapp.ui.servercheck.ServerCheckScreen

object Routes {
    const val SERVER_CHECK = "server_check"
    const val LOGIN = "login"
    const val HOME = "home"
    const val ORDEN_DETAIL = "orden/{id}"
    const val ADMIN_DASHBOARD = "admin/dashboard"
    const val ADMIN_ALERTAS = "admin/alertas"
    const val ADMIN_EQUIPOS = "admin/equipos"
    const val ADMIN_PROGRAMAS = "admin/programas"
    const val ADMIN_REPUESTOS = "admin/repuestos"
    const val ADMIN_REPUESTOS_CONSOLIDADO = "admin/repuestos/consolidado"
    const val ADMIN_PROVEEDORES = "admin/proveedores"
    const val ADMIN_REPUESTO_PROVEEDORES = "admin/repuestos/{repuestoId}/proveedores?nombre={nombre}"
    const val ADMIN_TECNICOS = "admin/tecnicos"
    const val ADMIN_GENERAR = "admin/generar"
    const val ADMIN_HISTORIAL = "admin/equipos/{equipoId}/historial?nombre={nombre}"
    const val ADMIN_REPUESTOS_EQUIPO = "admin/equipos/{equipoId}/repuestos?nombre={nombre}"
    const val ADMIN_ELECTRICIDAD = "admin/electricidad"

    fun ordenDetail(id: Int) = "orden/$id"
    fun historialEquipo(id: Int, nombre: String) = "admin/equipos/$id/historial?nombre=${java.net.URLEncoder.encode(nombre, "UTF-8")}"
    fun repuestosEquipo(id: Int, nombre: String) = "admin/equipos/$id/repuestos?nombre=${java.net.URLEncoder.encode(nombre, "UTF-8")}"
    fun repuestoProveedores(id: Int, nombre: String) = "admin/repuestos/$id/proveedores?nombre=${java.net.URLEncoder.encode(nombre, "UTF-8")}"
}

@Composable
fun AppNavigation(navController: NavHostController) {
    NavHost(navController = navController, startDestination = Routes.SERVER_CHECK) {

        composable(Routes.SERVER_CHECK) {
            ServerCheckScreen(
                onConnectedLoggedIn = { navController.navigate(Routes.HOME) { popUpTo(Routes.SERVER_CHECK) { inclusive = true } } },
                onConnectedNeedLogin = { navController.navigate(Routes.LOGIN) { popUpTo(Routes.SERVER_CHECK) { inclusive = true } } }
            )
        }

        composable(Routes.LOGIN) {
            LoginScreen(onLoginSuccess = { navController.navigate(Routes.HOME) { popUpTo(Routes.LOGIN) { inclusive = true } } })
        }

        composable(Routes.HOME) {
            HomeScreen(
                onOrdenClick = { id -> navController.navigate(Routes.ordenDetail(id)) },
                onNavigateToAdminDashboard = { navController.navigate(Routes.ADMIN_DASHBOARD) },
                onNavigateToAdminAlertas = { navController.navigate(Routes.ADMIN_ALERTAS) },
                onNavigateToAdminEquipos = { navController.navigate(Routes.ADMIN_EQUIPOS) },
                onNavigateToAdminProgramas = { navController.navigate(Routes.ADMIN_PROGRAMAS) },
                onNavigateToAdminRepuestos = { navController.navigate(Routes.ADMIN_REPUESTOS) },
                onNavigateToConsolidado = { navController.navigate(Routes.ADMIN_REPUESTOS_CONSOLIDADO) },
                onNavigateToProveedores = { navController.navigate(Routes.ADMIN_PROVEEDORES) },
                onNavigateToAdminTecnicos = { navController.navigate(Routes.ADMIN_TECNICOS) },
                onNavigateToGenerarOrdenes = { navController.navigate(Routes.ADMIN_GENERAR) },
                onNavigateToElectricidad = { navController.navigate(Routes.ADMIN_ELECTRICIDAD) },
                onNavigateToExportImportDb = { /* TODO */ },
                onLogout = { navController.navigate(Routes.SERVER_CHECK) { popUpTo(Routes.HOME) { inclusive = true } } }
            )
        }

        composable(Routes.ORDEN_DETAIL, arguments = listOf(navArgument("id") { type = NavType.IntType })) { back ->
            OrdenDetailScreen(ordenId = back.arguments!!.getInt("id"), onBack = { navController.popBackStack() })
        }

        composable(Routes.ADMIN_DASHBOARD) { DashboardScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_ALERTAS) { AlertasScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_EQUIPOS) {
            EquiposAdminScreen(
                onBack = { navController.popBackStack() },
                onHistorial = { id, nombre -> navController.navigate(Routes.historialEquipo(id, nombre)) },
                onRepuestosEquipo = { id, nombre -> navController.navigate(Routes.repuestosEquipo(id, nombre)) }
            )
        }
        composable(Routes.ADMIN_PROGRAMAS) { ProgramasAdminScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_REPUESTOS) {
            RepuestosAdminScreen(
                onBack = { navController.popBackStack() },
                onProveedores = { id, nombre -> navController.navigate(Routes.repuestoProveedores(id, nombre)) }
            )
        }
        composable(Routes.ADMIN_REPUESTOS_CONSOLIDADO) { ConsolidadoRepuestosScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_PROVEEDORES) { ProveedoresAdminScreen(onBack = { navController.popBackStack() }) }
        composable(
            route = "admin/repuestos/{repuestoId}/proveedores?nombre={nombre}",
            arguments = listOf(
                navArgument("repuestoId") { type = NavType.IntType },
                navArgument("nombre") { defaultValue = "" }
            )
        ) { back ->
            RepuestoProveedoresScreen(
                repuestoId = back.arguments!!.getInt("repuestoId"),
                repuestoNombre = back.arguments!!.getString("nombre") ?: "",
                onBack = { navController.popBackStack() }
            )
        }
        composable(
            route = "admin/equipos/{equipoId}/repuestos?nombre={nombre}",
            arguments = listOf(
                navArgument("equipoId") { type = NavType.IntType },
                navArgument("nombre") { defaultValue = "" }
            )
        ) { back ->
            RepuestosEquipoScreen(
                equipoId = back.arguments!!.getInt("equipoId"),
                equipoNombre = back.arguments!!.getString("nombre") ?: "",
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.ADMIN_TECNICOS) { TecnicosAdminScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_GENERAR) { GenerarOrdenesScreen(onBack = { navController.popBackStack() }) }
        composable(Routes.ADMIN_ELECTRICIDAD) {
            // Placeholder hasta tener ElectricidadScreen
            androidx.compose.material3.Text("Electricidad - próximamente")
        }
        composable(
            route = "admin/equipos/{equipoId}/historial?nombre={nombre}",
            arguments = listOf(
                navArgument("equipoId") { type = NavType.IntType },
                navArgument("nombre") { defaultValue = "" }
            )
        ) { back ->
            HistorialEquipoScreen(
                equipoId = back.arguments!!.getInt("equipoId"),
                equipoNombre = back.arguments!!.getString("nombre") ?: "",
                onBack = { navController.popBackStack() },
                onOrdenClick = { id -> navController.navigate(Routes.ordenDetail(id)) }
            )
        }
    }
}
