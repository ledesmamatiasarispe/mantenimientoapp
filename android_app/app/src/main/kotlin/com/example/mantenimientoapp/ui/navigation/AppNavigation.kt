package com.example.mantenimientoapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.mantenimientoapp.ui.admin.equipos.EquiposAdminScreen
import com.example.mantenimientoapp.ui.admin.programas.ProgramasAdminScreen
import com.example.mantenimientoapp.ui.admin.repuestos.RepuestosAdminScreen
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
    const val ADMIN_EQUIPOS = "admin/equipos"
    const val ADMIN_PROGRAMAS = "admin/programas"
    const val ADMIN_REPUESTOS = "admin/repuestos"
    const val ADMIN_TECNICOS = "admin/tecnicos"

    fun ordenDetail(id: Int) = "orden/$id"
}

@Composable
fun AppNavigation(navController: NavHostController) {

    NavHost(
        navController = navController,
        startDestination = Routes.SERVER_CHECK
    ) {
        // 1. Verificación de servidor (siempre primero)
        composable(Routes.SERVER_CHECK) {
            ServerCheckScreen(
                onConnectedLoggedIn = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(Routes.SERVER_CHECK) { inclusive = true }
                    }
                },
                onConnectedNeedLogin = {
                    navController.navigate(Routes.LOGIN) {
                        popUpTo(Routes.SERVER_CHECK) { inclusive = true }
                    }
                }
            )
        }

        // 2. Login
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(Routes.LOGIN) { inclusive = true }
                    }
                }
            )
        }

        // 3. Home principal
        composable(Routes.HOME) {
            HomeScreen(
                onOrdenClick = { id -> navController.navigate(Routes.ordenDetail(id)) },
                onNavigateToAdminEquipos = { navController.navigate(Routes.ADMIN_EQUIPOS) },
                onNavigateToAdminProgramas = { navController.navigate(Routes.ADMIN_PROGRAMAS) },
                onNavigateToAdminRepuestos = { navController.navigate(Routes.ADMIN_REPUESTOS) },
                onNavigateToAdminTecnicos = { navController.navigate(Routes.ADMIN_TECNICOS) },
                onLogout = {
                    navController.navigate(Routes.SERVER_CHECK) {
                        popUpTo(Routes.HOME) { inclusive = true }
                    }
                }
            )
        }

        // 4. Detalle de orden
        composable(
            route = Routes.ORDEN_DETAIL,
            arguments = listOf(navArgument("id") { type = NavType.IntType })
        ) { backStack ->
            val ordenId = backStack.arguments!!.getInt("id")
            OrdenDetailScreen(
                ordenId = ordenId,
                onBack = { navController.popBackStack() }
            )
        }

        // 5. Admin sub-pantallas
        composable(Routes.ADMIN_EQUIPOS) {
            EquiposAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_PROGRAMAS) {
            ProgramasAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_REPUESTOS) {
            RepuestosAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_TECNICOS) {
            TecnicosAdminScreen(onBack = { navController.popBackStack() })
        }
    }
}
