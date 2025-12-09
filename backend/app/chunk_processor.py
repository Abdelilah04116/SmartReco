"""Chunk-based processing for large CSV files."""
from __future__ import annotations

from typing import Iterator, Callable, Optional, Dict, Any, List
import pandas as pd
from loguru import logger


class ChunkProcessor:
    """Process large DataFrames in chunks to manage memory."""
    
    def __init__(self, chunk_size: int = 10000):
        """
        Initialize chunk processor.
        
        Args:
            chunk_size: Number of rows per chunk
        """
        self.chunk_size = chunk_size
    
    def process_csv_chunks(self, 
                          csv_content: str,
                          chunk_size: Optional[int] = None,
                          encoding: str = 'utf-8') -> Iterator[pd.DataFrame]:
        """
        Read CSV file in chunks.
        
        Args:
            csv_content: CSV file content as string
            chunk_size: Optional chunk size override
            encoding: File encoding
            
        Yields:
            DataFrame chunks
        """
        chunk_size = chunk_size or self.chunk_size
        
        try:
            from io import StringIO
            chunk_iterator = pd.read_csv(
                StringIO(csv_content),
                chunksize=chunk_size,
                encoding=encoding,
                low_memory=False
            )
            
            for i, chunk in enumerate(chunk_iterator):
                logger.debug(f"Processing chunk {i+1} with {len(chunk)} rows")
                yield chunk
                
        except Exception as e:
            logger.error(f"Error processing CSV chunks: {e}")
            raise ValueError(f"Failed to process CSV: {e}")
    
    def process_dataframe_chunks(self, 
                                 df: pd.DataFrame,
                                 chunk_size: Optional[int] = None) -> Iterator[pd.DataFrame]:
        """
        Split DataFrame into chunks.
        
        Args:
            df: Input DataFrame
            chunk_size: Optional chunk size override
            
        Yields:
            DataFrame chunks
        """
        chunk_size = chunk_size or self.chunk_size
        
        total_rows = len(df)
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            logger.debug(f"Processing chunk {i+1}/{num_chunks} with {len(chunk)} rows")
            yield chunk
    
    def process_with_function(self,
                             df: pd.DataFrame,
                             func: Callable[[pd.DataFrame], pd.DataFrame],
                             chunk_size: Optional[int] = None,
                             combine_results: bool = True) -> pd.DataFrame:
        """
        Process DataFrame chunks with a function and optionally combine results.
        
        Args:
            df: Input DataFrame
            func: Function to apply to each chunk
            chunk_size: Optional chunk size override
            combine_results: Whether to combine results into single DataFrame
            
        Returns:
            Processed DataFrame(s)
        """
        results = []
        
        for chunk in self.process_dataframe_chunks(df, chunk_size):
            processed_chunk = func(chunk)
            if combine_results:
                results.append(processed_chunk)
            else:
                yield processed_chunk
        
        if combine_results and results:
            combined = pd.concat(results, ignore_index=True)
            logger.info(f"Combined {len(results)} chunks into DataFrame with {len(combined)} rows")
            return combined
        
        return pd.DataFrame()
    
    def estimate_memory_usage(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Estimate memory usage of DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with memory statistics
        """
        memory_usage = df.memory_usage(deep=True)
        total_memory = memory_usage.sum()
        
        return {
            "total_memory_mb": float(total_memory / 1024**2),
            "total_memory_gb": float(total_memory / 1024**3),
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_per_row_kb": float(total_memory / len(df) / 1024) if len(df) > 0 else 0,
            "column_memory": {
                col: float(mem / 1024**2) 
                for col, mem in memory_usage.items() 
                if col != 'Index'
            }
        }


# Global chunk processor instance
chunk_processor = ChunkProcessor()

