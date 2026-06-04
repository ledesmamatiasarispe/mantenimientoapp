package com.example.mantenimientoapp.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mantenimientoapp.data.local.entity.MaintenanceItem
import com.example.mantenimientoapp.domain.repository.MaintenanceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MainViewModel @Inject constructor(
    private val repository: MaintenanceRepository
) : ViewModel() {

    val items: StateFlow<List<MaintenanceItem>> = repository.getAllItems()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addItem(title: String, description: String) {
        viewModelScope.launch {
            repository.insertItem(
                MaintenanceItem(
                    title = title,
                    description = description,
                    date = System.currentTimeMillis()
                )
            )
        }
    }

    fun deleteItem(item: MaintenanceItem) {
        viewModelScope.launch {
            repository.deleteItem(item)
        }
    }
}
