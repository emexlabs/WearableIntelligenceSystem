package com.google.mediapipe.apps.wearableai.database.voicecommand;

//originally from MXT: Memory Expansion Tools
//Jeremy Stairs (stairs1) and Cayden Pierce
//https://github.com/stairs1/memory-expansion-tools

import android.location.Location;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import java.util.Date;

import java.util.List;

@Dao
public interface VoiceCommandDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    long insert(VoiceCommandEntity voiceCommand);

    @Query("UPDATE VoiceCommandTable SET location = :location, address = :address WHERE id = :id")
    void update(long id, Location location, String address);

    @Query("DELETE FROM VoiceCommandTable")
    void deleteAll();

    @Query("SELECT * from VoiceCommandTable ORDER BY timestamp DESC")
    LiveData<List<VoiceCommandEntity>> getAllVoiceCommands();

    @Query("SELECT * from VoiceCommandTable ORDER BY timestamp DESC")
    List<VoiceCommandEntity> getAllVoiceCommandsSnapshot();
    
    @Query("SELECT * from VoiceCommandTable WHERE timestamp BETWEEN :startTime AND :endTime ORDER BY timestamp DESC")
    List<VoiceCommandEntity> getVoiceCommandRange(Date startTime, Date endTime);

    @Query("SELECT * from VoiceCommandTable WHERE command=:command ORDER BY timestamp DESC LIMIT 1")
    VoiceCommandEntity getLatestCommand(String command);

    @Query("SELECT * FROM VoiceCommandTable WHERE ID = :id")
    LiveData<VoiceCommandEntity> get_by_id(int id);
}
